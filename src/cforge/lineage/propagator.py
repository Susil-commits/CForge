"""Lineage Propagation Engine.

Propagates sensitivity and classification tags (e.g. PII) downstream across column lineage
with explainable reason chains and decay metrics.
"""

from typing import Dict, List, Set, Tuple, Any, Optional
from collections import deque
from cforge.lineage.parser import ColumnLineageEdge


class PropagatedTag:
    def __init__(self, target_table: str, target_column: str,
                 tag_name: str, tag_value: str,
                 confidence: float, hop_count: int,
                 reason_chain: List[str]):
        self.target_table = target_table
        self.target_column = target_column
        self.tag_name = tag_name
        self.tag_value = tag_value
        self.confidence = confidence
        self.hop_count = hop_count
        self.reason_chain = reason_chain

    def to_dict(self) -> Dict[str, Any]:
        return {
            "target": f"{self.target_table}.{self.target_column}",
            "table_name": self.target_table,
            "column_name": self.target_column,
            "tag_name": self.tag_name,
            "tag_value": self.tag_value,
            "confidence": round(self.confidence, 3),
            "hop_count": self.hop_count,
            "reason_chain": " -> ".join(self.reason_chain),
            "reason_steps": self.reason_chain
        }


class LineagePropagator:
    def __init__(self, edges: List[ColumnLineageEdge]):
        self.edges = edges
        self._build_graph()

    def _build_graph(self):
        """Construct adjacency lists for column-level graph."""
        self.downstream: Dict[str, List[ColumnLineageEdge]] = {}
        for edge in self.edges:
            src_key = f"{edge.source_table}.{edge.source_column}"
            if src_key not in self.downstream:
                self.downstream[src_key] = []
            self.downstream[src_key].append(edge)

    def propagate_tag(self, initial_table: str, initial_column: str,
                      tag_name: str = "PII", tag_value: str = "CONFIDENTIAL",
                      initial_confidence: float = 1.0, max_hops: int = 6) -> List[PropagatedTag]:
        """Trace tag downstream along column-level lineage graph."""
        root_key = f"{initial_table}.{initial_column}"
        propagated_results: List[PropagatedTag] = []
        visited: Set[str] = {root_key}

        # Queue contains: (current_key, current_table, current_col, current_conf, hop_count, chain)
        queue = deque([(
            root_key,
            initial_table,
            initial_column,
            initial_confidence,
            0,
            [f"{root_key} [{tag_name}:{tag_value}]"]
        )])

        while queue:
            curr_key, curr_tbl, curr_col, curr_conf, hops, chain = queue.popleft()

            if hops >= max_hops:
                continue

            outgoing = self.downstream.get(curr_key, [])
            for edge in outgoing:
                target_key = f"{edge.target_table}.{edge.target_column}"
                
                # Confidence adjustment based on transformation
                factor = 0.98 if edge.transformation_type == "DIRECT_COPY" else 0.90
                next_conf = curr_conf * factor
                next_hops = hops + 1
                next_chain = list(chain) + [f"{target_key} ({edge.transformation_type})"]

                prop = PropagatedTag(
                    target_table=edge.target_table,
                    target_column=edge.target_column,
                    tag_name=tag_name,
                    tag_value=tag_value,
                    confidence=next_conf,
                    hop_count=next_hops,
                    reason_chain=next_chain
                )
                propagated_results.append(prop)

                if target_key not in visited:
                    visited.add(target_key)
                    queue.append((
                        target_key,
                        edge.target_table,
                        edge.target_column,
                        next_conf,
                        next_hops,
                        next_chain
                    ))

        return propagated_results
