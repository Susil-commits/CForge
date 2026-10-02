"""Universal Catalog Adapter Interface.

Defines the pluggable abstraction for bidirectional synchronization of assets,
tags, business glossary terms, and column-level lineage with enterprise catalogs.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from cforge.catalog.models import Asset, Tag, GlossaryTerm, LineageEdge


class BaseCatalogAdapter(ABC):
    """Abstract Base Class for enterprise catalog adapters (DataHub, OpenMetadata, Atlan, File)."""

    @abstractmethod
    def pull_assets(self) -> List[Asset]:
        """Retrieve all catalog assets from the target system."""
        pass

    @abstractmethod
    def push_assets(self, assets: List[Asset]) -> bool:
        """Publish assets to the target catalog system."""
        pass

    @abstractmethod
    def pull_tags(self) -> List[Tag]:
        """Retrieve sensitivity and governance classifications."""
        pass

    @abstractmethod
    def push_tags(self, tags: List[Tag]) -> bool:
        """Publish classifications and governance tags."""
        pass

    @abstractmethod
    def pull_glossary(self) -> List[GlossaryTerm]:
        """Retrieve business glossary terms."""
        pass

    @abstractmethod
    def push_glossary(self, terms: List[GlossaryTerm]) -> bool:
        """Publish business glossary terms."""
        pass

    @abstractmethod
    def pull_lineage(self) -> List[LineageEdge]:
        """Retrieve column-level lineage graph edges."""
        pass

    @abstractmethod
    def push_lineage(self, edges: List[LineageEdge]) -> bool:
        """Publish lineage graph edges."""
        pass
