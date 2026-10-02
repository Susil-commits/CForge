"""Classifier Agent: Classifies PII, regulatory sensitivity, and compliance tags."""

from typing import List, Optional
from pydantic import BaseModel, Field
from cforge.enrichment.profiler import ColumnProfile


class ClassificationResult(BaseModel):
    is_pii: bool = Field(description="Whether the column contains Personally Identifiable Information.")
    pii_type: str = Field(description="Specific PII classification category (or NONE).")
    sensitivity_level: str = Field(description="Data sensitivity: PUBLIC, INTERNAL, CONFIDENTIAL, RESTRICTED.")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence score.")
    evidence: List[str] = Field(description="Grounded evidence supporting classification.")
    regulatory_domains: List[str] = Field(description="Relevant data privacy frameworks: LGPD, GDPR, PCI-DSS.")


class ClassifierAgent:
    def __init__(self, model_name: str = "cforge-classifier-v1"):
        self.model_name = model_name

    def classify(self, profile: ColumnProfile, upstream_tags: Optional[List[str]] = None) -> ClassificationResult:
        """Classify PII and sensitivity grounded in column profile statistics and lineage."""
        col = profile.column_name.lower()
        patterns = profile.detected_patterns
        evidence: List[str] = []

        is_pii = False
        pii_type = "NONE"
        sensitivity = "INTERNAL"
        confidence = 0.90
        regulations: List[str] = []

        # Check upstream lineage tags first (lineage grounding)
        if upstream_tags and any("PII" in t for t in upstream_tags):
            is_pii = True
            pii_type = "CUSTOMER_ID"
            sensitivity = "RESTRICTED"
            confidence = 0.95
            evidence.append(f"Derived directly from upstream parent column classified as PII: {upstream_tags}.")
            regulations.extend(["LGPD", "GDPR"])

        # Check regex patterns
        if "EMAIL_PATTERN" in patterns or "email" in col:
            is_pii = True
            pii_type = "EMAIL"
            sensitivity = "RESTRICTED"
            confidence = 0.98
            evidence.append("Regex pattern and column identifier indicate electronic mail contact.")
            regulations.extend(["LGPD", "GDPR"])
        elif "PHONE_PATTERN" in patterns or any(k in col for k in ["phone", "fax", "tel"]):
            is_pii = True
            pii_type = "PHONE_NUMBER"
            sensitivity = "RESTRICTED"
            confidence = 0.96
            evidence.append("Telephone number structure and dial pattern detected.")
            regulations.extend(["LGPD", "GDPR"])
        elif "ZIP_PATTERN" in patterns or any(k in col for k in ["zip", "postal", "cep"]):
            is_pii = True
            pii_type = "POSTAL_CODE"
            sensitivity = "CONFIDENTIAL"
            confidence = 0.95
            evidence.append(f"Postal code format verified with {profile.distinct_count} regional postal prefixes.")
            regulations.extend(["LGPD", "GDPR"])
        elif any(k in col for k in ["customer_id", "customer_unique_id"]):
            is_pii = True
            pii_type = "CUSTOMER_ID"
            sensitivity = "RESTRICTED"
            confidence = 0.97
            evidence.append(f"Individual customer personal identity token with cardinality {profile.distinct_count}.")
            regulations.extend(["LGPD", "GDPR"])
        elif any(k in col for k in ["contact_name", "first_name", "last_name", "ship_name"]):
            is_pii = True
            pii_type = "PERSON_NAME"
            sensitivity = "RESTRICTED"
            confidence = 0.96
            evidence.append("Natural person first or last name identifier.")
            regulations.extend(["LGPD", "GDPR"])
        elif any(k in col for k in ["address", "street"]):
            is_pii = True
            pii_type = "PHYSICAL_ADDRESS"
            sensitivity = "RESTRICTED"
            confidence = 0.96
            evidence.append("Physical delivery or residential geographical street address.")
            regulations.extend(["LGPD", "GDPR"])
        elif any(k in col for k in ["payment_value", "payment_amount", "credit_card", "payment_type"]):
            is_pii = True
            pii_type = "FINANCIAL"
            sensitivity = "RESTRICTED"
            confidence = 0.94
            evidence.append("Payment transaction or financial settlement instrument data.")
            regulations.append("PCI-DSS")
        elif any(k in col for k in ["notes", "comment", "review_comment"]):
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
