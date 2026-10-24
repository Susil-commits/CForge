"""Classifier Agent: Classifies PII, regulatory sensitivity, and compliance tags.

Provides both an LLM-powered agent with schema validation and a heuristic baseline agent.
"""

import re

from pydantic import BaseModel, Field

from cforge.enrichment.profiler import ColumnProfile
from cforge.llm.client import LLMAuthenticationError, LLMClient


class ClassificationResult(BaseModel):
    is_pii: bool = Field(description="Whether the column contains Personally Identifiable Information.")
    pii_type: str = Field(description="Specific PII classification category: CUSTOMER_ID, PERSON_NAME, EMAIL, PHONE_NUMBER, POSTAL_CODE, PHYSICAL_ADDRESS, FINANCIAL, CONFIDENTIAL_NOTES, NONE.")
    sensitivity_level: str = Field(description="Data sensitivity: PUBLIC, INTERNAL, CONFIDENTIAL, RESTRICTED.")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence score.")
    evidence: list[str] = Field(description="Grounded evidence supporting classification.")
    regulatory_domains: list[str] = Field(description="Relevant data privacy frameworks: LGPD, GDPR, PCI-DSS.")


class HeuristicClassifierAgent:
    """Keyword, regex, and rule-based baseline classifier agent."""

    def __init__(self, model_name: str = "heuristic-rule-baseline"):
        self.model_name = model_name

    def classify(self, profile: ColumnProfile, upstream_tags: list[str] | None = None) -> ClassificationResult:
        """Classify PII and sensitivity grounded in column profile statistics and lineage."""
        col_clean = re.sub(r"[^a-zA-Z0-9]", "", profile.column_name).lower()
        patterns = profile.detected_patterns
        evidence: list[str] = []

        is_pii = False
        pii_type = "NONE"
        sensitivity = "INTERNAL"
        confidence = 0.90
        regulations: list[str] = []

        if upstream_tags and any("PII" in t for t in upstream_tags):
            is_pii = True
            pii_type = "CUSTOMER_ID"
            sensitivity = "RESTRICTED"
            confidence = 0.95
            evidence.append(f"Derived directly from upstream parent column classified as PII: {upstream_tags}.")
            regulations.extend(["LGPD", "GDPR"])

        if "EMAIL_PATTERN" in patterns or "email" in col_clean:
            is_pii = True
            pii_type = "EMAIL"
            sensitivity = "RESTRICTED"
            confidence = 0.98
            evidence.append("Regex pattern and column identifier indicate electronic mail contact.")
            regulations.extend(["LGPD", "GDPR"])
        elif any(k in col_clean for k in ["phone", "fax", "tel"]) or ("PHONE_PATTERN" in patterns and not any(k in col_clean for k in ["id", "count", "num"])):
            is_pii = True
            pii_type = "PHONE_NUMBER"
            sensitivity = "RESTRICTED"
            confidence = 0.96
            evidence.append("Telephone number structure and dial pattern detected.")
            regulations.extend(["LGPD", "GDPR"])
        elif any(k in col_clean for k in ["zip", "postal", "cep"]):
            is_pii = True
            pii_type = "POSTAL_CODE"
            sensitivity = "CONFIDENTIAL"
            confidence = 0.95
            evidence.append(f"Postal code format verified with {profile.distinct_count} regional postal prefixes.")
            regulations.extend(["LGPD", "GDPR"])
        elif any(k in col_clean for k in ["customerid", "customeruniqueid"]):
            is_pii = True
            pii_type = "CUSTOMER_ID"
            sensitivity = "RESTRICTED"
            confidence = 0.97
            evidence.append(f"Individual customer personal identity token with cardinality {profile.distinct_count}.")
            regulations.extend(["LGPD", "GDPR"])
        elif any(k in col_clean for k in ["contactname", "firstname", "lastname", "shipname"]):
            is_pii = True
            pii_type = "PERSON_NAME"
            sensitivity = "RESTRICTED"
            confidence = 0.96
            evidence.append("Natural person first or last name identifier.")
            regulations.extend(["LGPD", "GDPR"])
        elif any(k in col_clean for k in ["address", "street"]):
            is_pii = True
            pii_type = "PHYSICAL_ADDRESS"
            sensitivity = "RESTRICTED"
            confidence = 0.96
            evidence.append("Physical delivery or residential geographical street address.")
            regulations.extend(["LGPD", "GDPR"])
        elif any(k in col_clean for k in ["birthdate", "dob"]):
            is_pii = True
            pii_type = "CONFIDENTIAL_NOTES"
            sensitivity = "CONFIDENTIAL"
            confidence = 0.95
            evidence.append("Personal birth date or demographic milestone.")
            regulations.extend(["LGPD", "GDPR"])
        elif any(k in col_clean for k in ["paymentvalue", "paymentamount", "creditcard", "paymenttype"]):
            is_pii = True
            pii_type = "FINANCIAL"
            sensitivity = "RESTRICTED"
            confidence = 0.94
            evidence.append("Payment transaction or financial settlement instrument data.")
            regulations.append("PCI-DSS")
        elif any(k in col_clean for k in ["notes", "comment", "reviewcomment"]):
            is_pii = True
            pii_type = "CONFIDENTIAL_NOTES"
            sensitivity = "CONFIDENTIAL"
            confidence = 0.91
            evidence.append("Unstructured free-form text with potential unredacted customer commentary.")
            regulations.extend(["LGPD", "GDPR"])
        else:
            is_pii = False
            pii_type = "NONE"
            sensitivity = "INTERNAL"
            confidence = 0.92
            evidence.append("Column attributes do not contain identifiable personal individual traits.")

        evidence.append(f"Profile null rate: {profile.null_percentage}%, uniqueness flag: {profile.is_unique}.")

        return ClassificationResult(
            is_pii=is_pii,
            pii_type=pii_type,
            sensitivity_level=sensitivity,
            confidence=confidence,
            evidence=evidence,
            regulatory_domains=list(set(regulations))
        )


class LLMClassifierAgent:
    """Real LLM-powered privacy and PII classification agent."""

    SYSTEM_PROMPT = """You are an expert Data Privacy & Governance Classifier.
Analyze the column profile to identify Personally Identifiable Information (PII) under GDPR and LGPD frameworks.

Classification Taxonomies:
- CUSTOMER_ID: Unique customer tokens or account IDs identifying individual persons.
- PERSON_NAME: Individual person first names, last names, recipient contact names.
- EMAIL: Electronic mail contact addresses.
- PHONE_NUMBER: Direct phone, mobile, fax numbers.
- POSTAL_CODE: Detailed residential/delivery postal routing codes (CEP / Zip).
- PHYSICAL_ADDRESS: Street addresses, residential apartment, delivery locations.
- FINANCIAL: Payment card instruments, payment monetary amounts, financing installment details.
- CONFIDENTIAL_NOTES: Free-form review feedback or customer messages with potential personal disclosures.
- NONE: Non-personal operational data, product SKUs, seller IDs, date timestamps, status codes, metrics.

Sensitivity Levels:
- RESTRICTED: Direct PII or financial data requiring masking & strict access gates.
- CONFIDENTIAL: Indirect PII or sensitive feedback requiring need-to-know controls.
- INTERNAL: Standard enterprise operational data.
- PUBLIC: Publicly open reference tables.
"""

    def __init__(self, model_name: str | None = None):
        self.client = LLMClient(model_name=model_name)

    def classify(self, profile: ColumnProfile, upstream_tags: list[str] | None = None) -> ClassificationResult:
        """Call LLM with JSON-schema validation to classify column privacy & PII."""
        user_prompt = f"""Table: {profile.table_name}
Column: {profile.column_name}
Data Type: {profile.data_type}
Total Rows: {profile.total_rows}
Null Rate: {profile.null_percentage}%
Distinct Values: {profile.distinct_count} (Unique Key: {profile.is_unique})
Min Value: {profile.min_value}
Max Value: {profile.max_value}
Avg Value: {profile.avg_value}
Detected Patterns: {profile.detected_patterns}
Sample Values: {profile.sample_values[:5] if profile.sample_values else []}
Neighbor Columns: {profile.neighbor_columns[:6]}
Upstream Tags: {upstream_tags or []}

Classify this column adhering to the schema.
"""
        response = self.client.generate_structured(
            system_prompt=self.SYSTEM_PROMPT,
            user_prompt=user_prompt,
            response_model=ClassificationResult
        )
        return response.parsed


class ClassifierAgent:
    """Facade Classifier Agent with configurable execution mode ('auto', 'llm', 'heuristic')."""

    def __init__(self, model_name: str = "cforge-classifier-v1", mode: str = "heuristic"):
        self.model_name = model_name
        self.mode = mode
        self.heuristic_agent = HeuristicClassifierAgent(model_name)
        self.llm_agent = LLMClassifierAgent()

    def classify(self, profile: ColumnProfile, upstream_tags: list[str] | None = None) -> ClassificationResult:
        if self.mode == "heuristic":
            return self.heuristic_agent.classify(profile, upstream_tags)
        
        if self.mode == "llm":
            return self.llm_agent.classify(profile, upstream_tags)

        try:
            return self.llm_agent.classify(profile, upstream_tags)
        except LLMAuthenticationError:
            return self.heuristic_agent.classify(profile, upstream_tags)
        except Exception:
            return self.heuristic_agent.classify(profile, upstream_tags)
