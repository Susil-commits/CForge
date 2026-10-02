"""DuckDB Embedded Catalog Adapter.

Connects directly to the live ContextForge MetadataStore for high-performance synchronization.
"""

from typing import List, Dict, Any, Optional
from pathlib import Path
from cforge.adapters.base import BaseCatalogAdapter
from cforge.catalog.models import Asset, Tag, GlossaryTerm, LineageEdge
from cforge.catalog.store import MetadataStore
from cforge.config import METADATA_DB_PATH


class DuckDBCatalogAdapter(BaseCatalogAdapter):
    def __init__(self, db_path: Optional[Path] = None):
        self.store = MetadataStore(db_path or METADATA_DB_PATH)

    def pull_assets(self) -> List[Asset]:
        rows = self.store.conn.execute("""
            SELECT asset_id, parent_id, asset_type, name, display_name, description, data_type, owner, certification_status, quality_score, version
            FROM assets
        """).fetchall()
        assets = []
        for r in rows:
            assets.append(Asset(
                asset_id=r[0],
                parent_id=r[1],
                asset_type=r[2],
                name=r[3],
                display_name=r[4],
                description=r[5],
                data_type=r[6],
                owner=r[7],
                certification_status=r[8],
                quality_score=r[9],
                version=r[10]
            ))
        return assets

    def push_assets(self, assets: List[Asset]) -> bool:
        for a in assets:
            self.store.upsert_asset(a.model_dump(mode="json"))
        return True

    def pull_tags(self) -> List[Tag]:
        rows = self.store.conn.execute("""
            SELECT tag_id, asset_id, tag_name, tag_value, confidence, source, reason
            FROM tags
        """).fetchall()
        tags = []
        for r in rows:
            tags.append(Tag(
                tag_id=r[0],
                asset_id=r[1],
                tag_name=r[2],
                tag_value=r[3],
                confidence=r[4],
                source=r[5],
                reason=r[6]
            ))
        return tags

    def push_tags(self, tags: List[Tag]) -> bool:
        for t in tags:
            self.store.add_tag(
                asset_id=t.asset_id,
                tag_name=t.tag_name,
                tag_value=t.tag_value,
                confidence=t.confidence,
                source=t.source.value if hasattr(t.source, 'value') else str(t.source),
                reason=t.reason
            )
        return True

    def pull_glossary(self) -> List[GlossaryTerm]:
        rows = self.store.conn.execute("""
            SELECT term_id, term_name, definition, domain FROM glossary_terms
        """).fetchall()
        return [GlossaryTerm(term_id=r[0], term_name=r[1], definition=r[2], domain=r[3]) for r in rows]

    def push_glossary(self, terms: List[GlossaryTerm]) -> bool:
        for g in terms:
            self.store.conn.execute("""
                INSERT OR REPLACE INTO glossary_terms (term_id, term_name, definition, domain)
                VALUES (?, ?, ?, ?)
            """, (g.term_id, g.term_name, g.definition, g.domain))
        return True

    def pull_lineage(self) -> List[LineageEdge]:
        rows = self.store.conn.execute("""
            SELECT edge_id, source_asset_id, target_asset_id, transformation_type, transformation_logic
            FROM lineage_edges
        """).fetchall()
        return [
            LineageEdge(
                edge_id=r[0],
                source_asset_id=r[1],
                target_asset_id=r[2],
                transformation_type=r[3],
                transformation_logic=r[4]
            )
            for r in rows
        ]

    def push_lineage(self, edges: List[LineageEdge]) -> bool:
        for e in edges:
            self.store.add_lineage_edge(
                source_asset_id=e.source_asset_id,
                target_asset_id=e.target_asset_id,
                transformation_type=e.transformation_type,
                transformation_logic=e.transformation_logic
            )
        return True
