"""Metadata domain models for ContextForge."""

from enum import Enum
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from pydantic import BaseModel, Field


class AssetType(str, Enum):
    DATABASE = "DATABASE"
    SCHEMA = "SCHEMA"
    TABLE = "TABLE"
    COLUMN = "COLUMN"
    MODEL = "MODEL"
    DASHBOARD = "DASHBOARD"


class CertificationStatus(str, Enum):
    CERTIFIED = "CERTIFIED"
    IN_REVIEW = "IN_REVIEW"
    DRAFT = "DRAFT"
    DEPRECATED = "DEPRECATED"


class TagSource(str, Enum):
    AGENT = "AGENT"
    HUMAN_STEWARD = "HUMAN_STEWARD"
    PROPAGATED = "PROPAGATED"
    GOLD_STANDARD = "GOLD_STANDARD"


class Asset(BaseModel):
    asset_id: str
    parent_id: Optional[str] = None
    asset_type: AssetType
    name: str
    display_name: Optional[str] = None
    description: Optional[str] = None
    data_type: Optional[str] = None
    owner: Optional[str] = "Data Governance Guild"
    certification_status: CertificationStatus = CertificationStatus.DRAFT
    quality_score: float = 1.0
    version: int = 1
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Tag(BaseModel):
    tag_id: str
    asset_id: str
    tag_name: str
    tag_value: Optional[str] = None
    confidence: float = 1.0
    source: TagSource = TagSource.AGENT
    reason: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class GlossaryTerm(BaseModel):
    term_id: str
    term_name: str
    definition: str
    domain: str = "Enterprise E-Commerce"
    synonyms: List[str] = Field(default_factory=list)


class LineageEdge(BaseModel):
    edge_id: str
    source_asset_id: str
    target_asset_id: str
    transformation_type: str = "TRANSFORMATION"
    transformation_logic: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class AssetHistory(BaseModel):
    history_id: str
    asset_id: str
    version: int
    change_type: str
    changed_by: str
    before_state: Optional[Dict[str, Any]] = None
    after_state: Dict[str, Any]
    reason: Optional[str] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
