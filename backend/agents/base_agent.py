"""
Base Agent
==========
Foundation class for all LLM agents in the pipeline.
Handles:
  - Prompt construction (system + context + task)
  - Anthropic API calls with error handling
  - Response parsing and validation
  - Retry logic for API failures
  - Audit logging for every call

All creative agents and the judge agent inherit from this.
Shared logic lives here — DRY principle.
"""

import os
import time
from typing import Optional, Dict, Any, List

from anthropic import Anthropic
from dotenv import load_dotenv

from backend.pipeline.state import AuditEntry
from backend.observability.audit_log import (
    create_audit_entry,
    hash_prompt,
    truncate_for_snapshot,
)

# Load environment variables
load_dotenv()


class BaseAgent:
    """
    Base class for all pipeline agents.
    
    Each agent has three components (matching Pencil's architecture):
      - Instructions: The system prompt defining behavior
      - Knowledge: Context injected per-call (product truth, trends, etc.)
      - Tools: Capabilities the agent can use (API calls, validators)
    
    Usage:
        agent = BaseAgent(
            name="ads_agent",
            system_prompt="You are the creative voice of Dr. Jart+...",
            model="claude-sonnet-4-20250514",
            temperature=0.7,
        )
        response, audit = agent.call(
            user_prompt="Generate 3 headlines...",
            context={"product": "...", "trends": "..."},
        )
    """

    def __init__(
        self,
        name: str,
        system_prompt: str,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ):
        """
        Initialize the agent.
        
        Args:
            name: Agent identifier (e.g., "ads_agent", "judge_agent")
                  Used in audit log entries for tracing.
            system_prompt: The system-level instructions that define
                          this agent's behavior. Loaded from brand_voice.yaml
                          and customized per agent type.
            model: Anthropic model ID. Defaults to env var DEFAULT_MODEL
                   or claude-sonnet-4-20250514.
            temperature: Controls creativity vs consistency.
                        0.7 for creative agents (balanced).
                        0.3 for judge agent (more deterministic).
            max_tokens: Maximum response length.
                       2000 for ads/video/image prompts.
                       4000 for blog posts.
        """
        self.name = name
        self.system_prompt = system_prompt
        self.model = model or os.getenv("DEFAULT_MODEL", "claude-sonnet-4-20250514")
        self.temperature = temperature
        self.max_tokens = max_tokens
        
        # Initialize Anthropic client
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY not found in environment. "
                "Copy .env.example to .env and add your key."
            )
        self.client = Anthropic(api_key=api_key)

    def build_prompt(
        self,
        task: str,
        context: Dict[str, Any] = None,
        feedback: List[str] = None,
    ) -> str:
        """
        Assemble the complete user prompt from components.
        
        The prompt has three sections:
          1. Context block — product truth, trend data, sourced claims
          2. Task block — the specific generation/evaluation instruction
          3. Corrections block — feedback from previous failed attempts (if retry)
        
        The system prompt is sent separately via the API's system parameter.
        
        Args:
            task: The specific instruction for this call
            context: Dict of context to inject (product info, trends, etc.)
            feedback: List of correction strings from previous scoring failures
        
        Returns:
            Assembled user prompt string
        """
        sections = []

        # Section 1: Context injection (knowledge layer)
        if context:
            context_parts = []
            for key, value in context.items():
                if isinstance(value, list):
                    # Format lists cleanly (e.g., trend narratives, claims)
                    items = "\n".join(f"  - {item}" for item in value)
                    context_parts.append(f"{key.upper()}:\n{items}")
                elif isinstance(value, dict):
                    # Format dicts (e.g., product config)
                    items = "\n".join(f"  {k}: {v}" for k, v in value.items())
                    context_parts.append(f"{key.upper()}:\n{items}")
                else:
                    context_parts.append(f"{key.upper()}: {value}")
            
            sections.append("=== CONTEXT ===\n" + "\n\n".join(context_parts))

        # Section 2: Task instruction
        sections.append("=== TASK ===\n" + task)

        # Section 3: Corrections from previous failures (self-correction mechanism)
        if feedback and len(feedback) > 0:
            corrections = "\n".join(f"  - {fb}" for fb in feedback)
            sections.append(
                "=== CRITICAL CORRECTIONS FROM PREVIOUS ATTEMPT ===\n"
                "The previous version of this asset FAILED quality scoring.\n"
                "You MUST fix these specific issues:\n"
                f"{corrections}\n\n"
                "Do NOT repeat these mistakes. Address each correction explicitly."
            )

        return "\n\n".join(sections)

    def call(
        self,
        task: str,
        context: Dict[str, Any] = None,
        feedback: List[str] = None,
        max_api_retries: int = 2,
    ) -> tuple[str, AuditEntry]:
        """
        Execute an LLM call with full observability.
        
        This is the core method. It:
          1. Builds the prompt from components
          2. Calls the Anthropic API
          3. Handles API errors with retry
          4. Measures latency
          5. Creates an audit log entry
          6. Returns the response text + audit entry
        
        Args:
            task: The specific instruction
            context: Context to inject into the prompt
            feedback: Corrections from previous failures
            max_api_retries: How many times to retry on API error
                            (NOT the same as scoring retries — this handles
                            network failures, rate limits, etc.)
        
        Returns:
            Tuple of (response_text, audit_entry)
            
        Raises:
            RuntimeError: If all API retries are exhausted
        """
        # Build the complete prompt
        user_prompt = self.build_prompt(task, context, feedback)
        prompt_hash_value = hash_prompt(self.system_prompt + user_prompt)
        
        # Track attempts for API-level retry
        last_error = None
        
        for attempt in range(max_api_retries + 1):
            start_time = time.time()
            
            try:
                # Make the API call
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=self.max_tokens,
                    temperature=self.temperature,
                    system=self.system_prompt,
                    messages=[
                        {"role": "user", "content": user_prompt}
                    ],
                )
                
                # Calculate latency
                latency_ms = int((time.time() - start_time) * 1000)
                
                # Extract text from response
                response_text = ""
                for block in response.content:
                    if block.type == "text":
                        response_text += block.text
                
                # Create audit entry
                audit = create_audit_entry(
                    node=self.name,
                    action="llm_call",
                    input_snapshot={
                        "system_prompt": truncate_for_snapshot(self.system_prompt, 200),
                        "user_prompt": truncate_for_snapshot(user_prompt),
                        "has_feedback": feedback is not None and len(feedback) > 0,
                        "feedback_count": len(feedback) if feedback else 0,
                    },
                    output_snapshot={
                        "response": truncate_for_snapshot(response_text),
                        "response_length": len(response_text),
                        "stop_reason": response.stop_reason,
                    },
                    model_used=self.model,
                    prompt_hash=prompt_hash_value,
                    latency_ms=latency_ms,
                    metadata={
                        "temperature": self.temperature,
                        "max_tokens": self.max_tokens,
                        "input_tokens": response.usage.input_tokens,
                        "output_tokens": response.usage.output_tokens,
                        "api_attempt": attempt + 1,
                    },
                )
                
                return response_text, audit
                
            except Exception as e:
                last_error = e
                latency_ms = int((time.time() - start_time) * 1000)
                
                if attempt < max_api_retries:
                    # Wait before retry (exponential backoff)
                    wait_time = 2 ** attempt  # 1s, 2s, 4s
                    time.sleep(wait_time)
                    continue
        
        # All retries exhausted — create error audit entry and raise
        error_audit = create_audit_entry(
            node=self.name,
            action="llm_call_failed",
            input_snapshot={
                "user_prompt": truncate_for_snapshot(user_prompt),
            },
            output_snapshot={
                "error": str(last_error),
                "attempts": max_api_retries + 1,
            },
            model_used=self.model,
            prompt_hash=prompt_hash_value,
            latency_ms=latency_ms,
            metadata={"final_error": str(last_error)},
        )
        
        raise RuntimeError(
            f"Agent '{self.name}' failed after {max_api_retries + 1} attempts: {last_error}"
        )

    def call_json(
        self,
        task: str,
        context: Dict[str, Any] = None,
        feedback: List[str] = None,
    ) -> tuple[dict, AuditEntry]:
        """
        Execute an LLM call and parse the response as JSON.
        Used by the judge agent which returns structured scores.
        
        Handles common LLM JSON issues:
          - Strips markdown code fences (```json ... ```)
          - Strips leading/trailing whitespace
          - Provides clear error on parse failure
        
        Returns:
            Tuple of (parsed_dict, audit_entry)
            
        Raises:
            ValueError: If response cannot be parsed as JSON
        """
        import json
        
        response_text, audit = self.call(task, context, feedback)
        
        # Clean common LLM JSON issues
        cleaned = response_text.strip()
        
        # Remove markdown code fences if present
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        elif cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()
        
        try:
            parsed = json.loads(cleaned)
            
            # Update audit entry with parse success
            audit.metadata["json_parse"] = "success"
            
            return parsed, audit
            
        except json.JSONDecodeError as e:
            # Update audit entry with parse failure
            audit.metadata["json_parse"] = "failed"
            audit.metadata["json_error"] = str(e)
            audit.metadata["raw_response"] = response_text
            
            raise ValueError(
                f"Agent '{self.name}' returned invalid JSON. "
                f"Error: {e}\n"
                f"Raw response: {response_text[:500]}"
            )
"""

---

## Let Me Walk Through the Key Design Decisions

### Why `call()` Returns a Tuple `(response_text, audit_entry)`
'''
Most LLM wrappers just return the text. You return both the response AND a structured log entry. The calling node doesn't have to construct its own log — it just appends the audit entry to the state. This means:

- Every LLM call is automatically logged with full details
- The node can add to the audit entry's metadata if needed
- Nothing falls through the cracks — if `call()` was invoked, there's a log

### Why Two Call Methods: `call()` and `call_json()`

Creative agents (ads, video, image, blog) return free-form text. The judge agent returns structured JSON scores. Rather than forcing JSON parsing into every call, you have:

- `call()` → returns raw text. Used by creative agents.
- `call_json()` → calls `call()`, then parses the response as JSON. Used by judge agent.

The JSON parsing handles real LLM quirks — sometimes Claude wraps JSON in code fences, sometimes there's trailing whitespace. The `call_json` method handles these edge cases so the judge agent doesn't have to.

### Why API Retry Is Separate from Scoring Retry

There are **two different retry loops** in this system:
```
API retry (inside base_agent.py):
  "The network failed or Anthropic returned a 500 error"
  → Wait and try the same call again
  → Max 2 retries with exponential backoff (1s, 2s)
  → This is infrastructure-level error handling

Scoring retry (inside route_decision.py):
  "The LLM generated content that failed quality checks"
  → Inject feedback, change the prompt, regenerate
  → Max 3 retries with targeted corrections
  → This is content-quality-level error handling
```

These are completely different concerns. Conflating them would be bad engineering. Dan might notice this separation — it shows you think about failure modes at the right abstraction level.

### Why `build_prompt()` Has Three Sections

The prompt is assembled from three distinct blocks:
```
=== CONTEXT ===              ← Knowledge layer (product truth, trends)
Product name: Ceramidin™...   Same for every call. Changes only when
Trend narratives: ...         you swap the product.

=== TASK ===                 ← Instruction layer
Generate 3 headlines...       Specific to the asset type.
                              Different for ads vs blog vs video.

=== CRITICAL CORRECTIONS === ← Self-correction layer (only on retry)
Fix these issues:             Only present when feedback exists.
- Headline 2 exceeds 30...   Grows with each iteration.

"""