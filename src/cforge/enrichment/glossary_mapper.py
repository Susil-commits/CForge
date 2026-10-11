"""Glossary Mapper Agent: Maps columns to standard enterprise business terms.

Provides both an LLM-powered agent with schema validation and a heuristic baseline agent.
"""

from typing import List, Dict, Optional
from pydantic import BaseModel, Field
from cforge.enrichment.profiler import ColumnProfile
from cforge.llm.client import LLMClient, LLMAuthenticationError


class GlossaryMappingResult(BaseModel):
    term_name: str = Field(description="Canonical enterprise glossary term name.")
    domain: str = Field(description="Business subject area domain.")
    definition: str = Field(description="Standardized definition of the term.")
    is_new_term: bool = Field(description="True if the term is newly proposed.")
    confidence: float = Field(ge=0.0, le=1.0, description="Mapping confidence score.")
    evidence: List[str] = Field(description="Evidence grounding this mapping.")


KNOWN_TERMS = {
    "customer_unique_id": ("Customer Master ID", "Customer Domain", "Permanent identifier representing the actual individual person across repeated purchases."),
    "customer_id": ("Customer Identifier", "Customer Domain", "Unique key assigned per order to identify purchasing customer."),
    "order_id": ("Order Identifier", "Fulfillment Domain", "Primary transactional key identifying a customer purchase event."),
    "price": ("Item Price", "Commerce Domain", "Base merchandise selling price in BRL excluding freight."),
    "item_price": ("Item Price", "Commerce Domain", "Base merchandise selling price in BRL excluding freight."),
    "freight_value": ("Freight Charge", "Logistics Domain", "Shipping logistics freight charge billed for transporting the item."),
    "review_score": ("Customer CSAT Score", "Customer Experience", "Satisfaction rating on a scale from 1 (terrible) to 5 (excellent)."),
    "payment_value": ("Payment Monetary Amount", "Finance Domain", "Total monetary amount charged on this specific payment transaction."),
    "grand_total_brl": ("Order Grand Total", "Finance Domain", "Total invoice amount (merchandise + freight) in BRL."),
    "total_lifetime_spend_brl": ("Customer Lifetime Spend", "Customer Analytics", "Cumulative monetary gross spend across all orders."),
    "state_code": ("State Code", "Geography Domain", "Two-letter state federative unit abbreviation."),
    "zip_code_prefix": ("Postal Code", "Geography Domain", "Five-digit postal routing prefix code.")
}


class HeuristicGlossaryMapperAgent:
    """Exact keyword and dictionary match baseline glossary agent."""

    def __init__(self, model_name: str = "heuristic-rule-baseline"):
        self.model_name = model_name

    def map_term(self, profile: ColumnProfile) -> GlossaryMappingResult:
        """Map column to existing enterprise terms or propose an ontology term."""
        col = profile.column_name.lower()
        evidence: List[str] = []

        if col in KNOWN_TERMS:
            name, domain, defn = KNOWN_TERMS[col]
            evidence.append(f"Direct match found in approved Enterprise Business Glossary for '{col}'.")
            return GlossaryMappingResult(
                term_name=name,
                domain=domain,
                definition=defn,
                is_new_term=False,
                confidence=0.98,
                evidence=evidence
            )

        clean_name = " ".join(w.capitalize() for w in col.split("_"))
        domain = "Operations Domain"
        if any(w in col for w in ["order", "item", "product"]):
            domain = "Merchandise & Order Domain"
        elif any(w in col for w in ["customer", "buyer", "user"]):
            domain = "Customer Domain"
        elif any(w in col for w in ["revenue", "price", "pay", "spend"]):
            domain = "Financial Analytics"
        elif any(w in col for w in ["delivery", "freight", "carrier", "ship"]):
            domain = "Logistics Domain"

        evidence.append(f"Derived canonical term from table '{profile.table_name}' and column '{profile.column_name}'.")
        evidence.append(f"Cardinality: {profile.distinct_count} distinct values, data type: {profile.data_type}.")

        return GlossaryMappingResult(
            term_name=clean_name,
            domain=domain,
            definition=f"Standard business attribute representing {clean_name.lower()} within {profile.table_name}.",
            is_new_term=True,
            confidence=0.88,
            evidence=evidence
        )


class LLMGlossaryMapperAgent:
    """Real LLM-powered enterprise glossary and semantic ontology mapping agent."""

    SYSTEM_PROMPT = """You are an Enterprise Business Glossary Ontology Agent.
Map the given table column to an approved enterprise glossary term if a semantic match exists, or propose a standardized business term and business domain.

Approved Glossary Terms & Definitions:
- Customer Master ID (Customer Domain): Permanent identifier representing the actual individual person across repeated purchases.
- Customer Identifier (Customer Domain): Key assigned per order to identify purchasing customer.
- Order Identifier (Fulfillment Domain): Primary transactional key identifying purchase event.
- Item Price (Commerce Domain): Base merchandise selling price excluding freight.
- Freight Charge (Logistics Domain): Shipping logistics freight charge billed for transporting the item.
- Customer CSAT Score (Customer Experience): Satisfaction rating on a scale from 1 (terrible) to 5 (excellent).
- Payment Monetary Amount (Finance Domain): Total monetary amount charged on transaction.
- Order Grand Total (Finance Domain): Total invoice amount (merchandise + freight).
- Customer Lifetime Spend (Customer Analytics): Cumulative monetary gross spend across all orders.
- State Code (Geography Domain): Two-letter state federative unit abbreviation.
- Postal Code (Geography Domain): Postal routing prefix code.
"""

    def __init__(self, model_name: Optional[str] = None):
        self.client = LLMClient(model_name=model_name)

    def map_term(self, profile: ColumnProfile) -> GlossaryMappingResult:
        """Call LLM with JSON-schema validation to map column to business glossary."""
        user_prompt = f"""Table: {profile.table_name}
Column: {profile.column_name}
Data Type: {profile.data_type}
Sample Values: {profile.sample_values[:5] if profile.sample_values else []}
Distinct Cardinality: {profile.distinct_count}
Min: {profile.min_value}, Max: {profile.max_value}, Avg: {profile.avg_value}

Map this column to an approved glossary term or propose a canonical standardized term adhering to the schema.
"""
        response = self.client.generate_structured(
            system_prompt=self.SYSTEM_PROMPT,
            user_prompt=user_prompt,
            response_model=GlossaryMappingResult
        )
        return response.parsed


class GlossaryMapperAgent:
    """Facade Glossary Mapper Agent with configurable execution mode ('auto', 'llm', 'heuristic')."""

    def __init__(self, model_name: str = "cforge-glossary-mapper-v1", mode: str = "auto"):
        self.model_name = model_name
        self.mode = mode
        self.heuristic_agent = HeuristicGlossaryMapperAgent(model_name)
        self.llm_agent = LLMGlossaryMapperAgent()

    def map_term(self, profile: ColumnProfile) -> GlossaryMappingResult:
        if self.mode == "heuristic":
            return self.heuristic_agent.map_term(profile)
        
        if self.mode == "llm":
            return self.llm_agent.map_term(profile)

        try:
            return self.llm_agent.map_term(profile)
        except LLMAuthenticationError:
            return self.heuristic_agent.map_term(profile)
        except Exception:
            return self.heuristic_agent.map_term(profile)
