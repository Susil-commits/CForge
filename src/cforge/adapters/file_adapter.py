"""File and JSON Catalog Adapter.

Provides portable file-based catalog synchronization for local workflows and backups.
"""

from typing import List, Dict, Any, Optional
from pathlib import Path
import json
from cforge.adapters.base import BaseCatalogAdapter
from cforge.catalog.models import Asset, Tag, GlossaryTerm, LineageEdge
from cforge.config import DATA_DIR


class FileJsonAdapter(BaseCatalogAdapter):
    def __init__(self, file_path: Optional[Path] = None):
        self.file_path = file_path or (DATA_DIR / "catalog_bundle.json")
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_file()

    def _ensure_file(self):
        if not self.file_path.exists():
            initial_data = {
                "assets": [],
                "tags": [],
                "glossary": [],
                "lineage": []
            }
            self.file_path.write_text(json.dumps(initial_data, indent=2), encoding="utf-8")

    def _read_data(self) -> Dict[str, Any]:
        return json.loads(self.file_path.read_text(encoding="utf-8"))

    def _write_data(self, data: Dict[str, Any]):
        self.file_path.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")

    def pull_assets(self) -> List[Asset]:
        data = self._read_data()
        return [Asset(**item) for item in data.get("assets", [])]

    def push_assets(self, assets: List[Asset]) -> bool:
        data = self._read_data()
        data["assets"] = [a.model_dump(mode="json") for a in assets]
        self._write_data(data)
        return True

    def pull_tags(self) -> List[Tag]:
        data = self._read_data()
        return [Tag(**item) for item in data.get("tags", [])]

    def push_tags(self, tags: List[Tag]) -> bool:
        data = self._read_data()
        data["tags"] = [t.model_dump(mode="json") for t in tags]
        self._write_data(data)
        return True

    def pull_glossary(self) -> List[GlossaryTerm]:
        data = self._read_data()
        return [GlossaryTerm(**item) for item in data.get("glossary", [])]

    def push_glossary(self, terms: List[GlossaryTerm]) -> bool:
        data = self._read_data()
        data["glossary"] = [g.model_dump(mode="json") for g in terms]
        self._write_data(data)
        return True

    def pull_lineage(self) -> List[LineageEdge]:
        data = self._read_data()
        return [LineageEdge(**item) for item in data.get("lineage", [])]

    def push_lineage(self, edges: List[LineageEdge]) -> bool:
        data = self._read_data()
        data["lineage"] = [e.model_dump(mode="json") for e in edges]
        self._write_data(data)
        return True
