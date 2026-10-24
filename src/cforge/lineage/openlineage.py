"""OpenLineage Standard Event Emitter.

Converts internal column-level lineage graph into standard OpenLineage RunEvents.
"""

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from cforge.config import DATA_DIR
from cforge.lineage.parser import ColumnLineageEdge


class OpenLineageEmitter:
    def __init__(self, namespace: str = "cforge.dataops"):
        self.namespace = namespace

    def create_run_event(self, job_name: str, input_tables: list[str],
                         output_table: str, edges: list[ColumnLineageEdge]) -> dict[str, Any]:
        """Construct a standard OpenLineage RunEvent with columnLineage facets."""
        run_id = str(uuid.uuid4())
        event_time = datetime.now(timezone.utc).isoformat()

        # Build columnLineage facet fields
        fields_facet: dict[str, Any] = {}
        for edge in edges:
            if edge.target_table == output_table:
                if edge.target_column not in fields_facet:
                    fields_facet[edge.target_column] = {
                        "inputFields": [],
                        "transformationDescription": edge.expression or edge.transformation_type,
                        "transformationType": edge.transformation_type
                    }
                fields_facet[edge.target_column]["inputFields"].append({
                    "namespace": self.namespace,
                    "name": edge.source_table,
                    "field": edge.source_column
                })

        event: dict[str, Any] = {
            "eventType": "COMPLETE",
            "eventTime": event_time,
            "run": {
                "runId": run_id,
                "facets": {}
            },
            "job": {
                "namespace": self.namespace,
                "name": f"model.{output_table}",
                "facets": {}
            },
            "inputs": [
                {
                    "namespace": self.namespace,
                    "name": inp,
                    "facets": {}
                }
                for inp in set(input_tables)
            ],
            "outputs": [
                {
                    "namespace": self.namespace,
                    "name": output_table,
                    "facets": {
                        "columnLineage": {
                            "_producer": "https://github.com/Susil-commits/CForge",
                            "_schemaURL": "https://openlineage.io/spec/facets/1-0-2/ColumnLineageDatasetFacet.json",
                            "fields": fields_facet
                        }
                    }
                }
            ],
            "producer": "https://github.com/Susil-commits/CForge"
        }
        return event

    def export_all_models_to_openlineage(self, edges_by_table: dict[str, list[ColumnLineageEdge]],
                                         output_file: Path | None = None) -> Path:
        """Export all model lineage events to a JSON file."""
        target_path = output_file or (DATA_DIR / "openlineage_events.json")
        target_path.parent.mkdir(parents=True, exist_ok=True)
        events = []

        for out_table, edges in edges_by_table.items():
            input_tables = list({e.source_table for e in edges})
            event = self.create_run_event(
                job_name=f"transform.{out_table}",
                input_tables=input_tables,
                output_table=out_table,
                edges=edges
            )
            events.append(event)

        target_path.write_text(json.dumps(events, indent=2), encoding="utf-8")
        return target_path
