"""
Product Truth Registry
======================
Loads and provides access to product_truth.yaml.
The anti-hallucination layer for product claims.
"""

import yaml
from pathlib import Path


class ProductTruthRegistry:
    """Loads product truth config and provides claim validation."""

    def __init__(self, config_path: str = "config/product_truth.yaml"):
        with open(config_path, "r") as f:
            self.config = yaml.safe_load(f)
        
        self.product = self.config.get("product", {})
        self.approved_claims = self.config.get("approved_claims", [])
        self.blocked_claims = self.config.get("blocked_claims", [])
        self.blocked_language = self.config.get("blocked_language", [])
        self.key_ingredients = self.config.get("key_ingredients", [])
        self.competitors = self.config.get("competitors", [])
        self.rules = self.config.get("rules", {})

    def is_claim_approved(self, claim: str) -> bool:
        """Check if a claim is in the approved list."""
        claim_lower = claim.lower()
        return any(approved.lower() in claim_lower for approved in self.approved_claims)

    def is_language_blocked(self, text: str) -> list:
        """Return any blocked terms found in text."""
        text_lower = text.lower()
        return [term for term in self.blocked_language if term.lower() in text_lower]

    def get_product_context(self) -> str:
        """Format product info for injection into agent prompts."""
        ingredients = "\n".join(
            f"  - {ing['name']}: {ing['function']}" for ing in self.key_ingredients
        )
        claims = "\n".join(f"  - {c}" for c in self.approved_claims)
        return (
            f"PRODUCT: {self.product.get('name', '')}\n"
            f"BRAND: {self.product.get('brand', '')}\n"
            f"PRICE: {self.product.get('price', '')}\n"
            f"KEY INGREDIENTS:\n{ingredients}\n"
            f"APPROVED CLAIMS:\n{claims}"
        )