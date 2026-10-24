"""Universal Catalog Adapter Interface.

Defines the pluggable abstraction for bidirectional synchronization of assets,
tags, business glossary terms, and column-level lineage with enterprise catalogs.
"""

from abc import ABC, abstractmethod

from cforge.catalog.models import Asset, GlossaryTerm, LineageEdge, Tag


class BaseCatalogAdapter(ABC):
    """Abstract Base Class for enterprise catalog adapters (DataHub, OpenMetadata, Atlan, File)."""

    @abstractmethod
    def pull_assets(self) -> list[Asset]:
        """Retrieve all catalog assets from the target system."""

    @abstractmethod
    def push_assets(self, assets: list[Asset]) -> bool:
        """Publish assets to the target catalog system."""

    @abstractmethod
    def pull_tags(self) -> list[Tag]:
        """Retrieve sensitivity and governance classifications."""

    @abstractmethod
    def push_tags(self, tags: list[Tag]) -> bool:
        """Publish classifications and governance tags."""

    @abstractmethod
    def pull_glossary(self) -> list[GlossaryTerm]:
        """Retrieve business glossary terms."""

    @abstractmethod
    def push_glossary(self, terms: list[GlossaryTerm]) -> bool:
        """Publish business glossary terms."""

    @abstractmethod
    def pull_lineage(self) -> list[LineageEdge]:
        """Retrieve column-level lineage graph edges."""

    @abstractmethod
    def push_lineage(self, edges: list[LineageEdge]) -> bool:
        """Publish lineage graph edges."""
