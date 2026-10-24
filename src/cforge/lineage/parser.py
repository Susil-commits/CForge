"""Column-Level Lineage Parser using sqlglot AST traversal.

Extracts column-to-column dependencies across SQL queries, CTEs, and table joins.
"""

from pathlib import Path
from typing import Any

from sqlglot import exp, parse_one
from sqlglot.lineage import lineage


class ColumnLineageEdge:
    def __init__(self, source_table: str, source_column: str,
                 target_table: str, target_column: str,
                 transformation_type: str = "DIRECT_COPY",
                 expression: str | None = None):
        self.source_table = source_table
        self.source_column = source_column
        self.target_table = target_table
        self.target_column = target_column
        self.transformation_type = transformation_type
        self.expression = expression

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": f"{self.source_table}.{self.source_column}",
            "target": f"{self.target_table}.{self.target_column}",
            "source_table": self.source_table,
            "source_column": self.source_column,
            "target_table": self.target_table,
            "target_column": self.target_column,
            "transformation_type": self.transformation_type,
            "expression": self.expression
        }

    def __repr__(self) -> str:
        return f"{self.source_table}.{self.source_column} -> {self.target_table}.{self.target_column} [{self.transformation_type}]"


class LineageParser:
    def __init__(self, dialect: str = "duckdb"):
        self.dialect = dialect

    def _resolve_column_through_ctes(self, col_name: str, table_ref: str, ctes: dict[str, exp.CTE], table_aliases: dict[str, str]) -> list[tuple[str, str]]:
        """Recursively trace a column reference through Common Table Expressions (CTEs) to find underlying physical tables."""
        if table_ref in ctes:
            cte = ctes[table_ref]
            selects = list(cte.this.find_all(exp.Select))
            sources = []
            for cte_select in selects:
                cte_aliases = {t.alias_or_name: t.name for t in cte_select.find_all(exp.Table) if t.name and t.alias_or_name}
                for cte_expr in cte_select.expressions:
                    if cte_expr.alias_or_name == col_name or (isinstance(cte_expr, exp.Column) and cte_expr.name == col_name):
                        for inner_col in cte_expr.find_all(exp.Column):
                            inner_tbl = cte_aliases.get(inner_col.table, inner_col.table or (list(cte_aliases.values())[0] if cte_aliases else "source"))
                            sources.extend(self._resolve_column_through_ctes(inner_col.name, inner_tbl, ctes, table_aliases))
            if sources:
                return sources
        real_tbl = table_aliases.get(table_ref, table_ref)
        return [(real_tbl, col_name)]

    def parse_query_lineage(self, target_table_name: str, sql_text: str) -> list[ColumnLineageEdge]:
        """Parse a SQL query and extract all column lineage edges targeting target_table_name."""
        edges: list[ColumnLineageEdge] = []
        try:
            tree = parse_one(sql_text, read=self.dialect)
        except Exception:
            return edges

        # Extract table aliases in FROM and JOINs
        table_aliases: dict[str, str] = {}
        for table in tree.find_all(exp.Table):
            t_name = table.name
            t_alias = table.alias_or_name
            if t_alias and t_name:
                table_aliases[t_alias] = t_name

        # Extract CTE names
        ctes: dict[str, exp.CTE] = {}
        for with_exp in tree.find_all(exp.With):
            for cte in with_exp.expressions:
                ctes[cte.alias] = cte

        # Extract projected columns in the outer SELECT
        outer_select = None
        if isinstance(tree, exp.Select):
            outer_select = tree
        else:
            # find first top-level select not inside a CTE
            for s in tree.find_all(exp.Select):
                outer_select = s
                break

        if not outer_select:
            return edges

        for expr in outer_select.expressions:
            col_alias = expr.alias_or_name
            if not col_alias:
                continue

            # Classify transformation type
            tx_type = "DIRECT_COPY"
            if isinstance(expr, exp.Alias):
                inner = expr.this
                if isinstance(inner, (exp.Count, exp.Sum, exp.Avg, exp.Min, exp.Max)):
                    tx_type = "AGGREGATION"
                elif isinstance(inner, (exp.Case, exp.Coalesce, exp.Cast, exp.Round)):
                    tx_type = "DERIVED_EXPRESSION"
                elif isinstance(inner, exp.Column):
                    tx_type = "DIRECT_COPY"
                else:
                    tx_type = "COMPUTED"
            elif isinstance(expr, (exp.Count, exp.Sum, exp.Avg, exp.Min, exp.Max)):
                tx_type = "AGGREGATION"

            sources: set[tuple[str, str]] = set()

            # 1. Use sqlglot lineage tool first
            try:
                node = lineage(col_alias, sql_text, dialect=self.dialect)
                for leaf in node.walk():
                    if leaf.name and leaf.name != col_alias:
                        # Extract table.col or col
                        name_parts = leaf.name.split(".")
                        if len(name_parts) == 2:
                            alias, c_name = name_parts
                            real_tbl = table_aliases.get(alias, alias)
                            sources.add((real_tbl, c_name))
                        elif len(name_parts) == 1 and table_aliases:
                            sources.add((list(table_aliases.values())[0], name_parts[0]))
            except Exception:
                pass

            # 2. Resilient CTE-aware traversal if sqlglot lineage threw or produced empty sources
            if not sources:
                for col_node in expr.find_all(exp.Column):
                    tbl_ref = col_node.table or (list(table_aliases.values())[0] if table_aliases else "source")
                    tbl_ref = table_aliases.get(tbl_ref, tbl_ref)
                    for r_tbl, r_col in self._resolve_column_through_ctes(col_node.name, tbl_ref, ctes, table_aliases):
                        sources.add((r_tbl, r_col))

            for s_tbl, s_col in sources:
                edges.append(ColumnLineageEdge(
                    source_table=s_tbl,
                    source_column=s_col,
                    target_table=target_table_name,
                    target_column=col_alias,
                    transformation_type=tx_type,
                    expression=expr.sql()
                ))

        return edges

    def parse_models_directory(self, models_dir: Path) -> list[ColumnLineageEdge]:
        """Parse all .sql files in the models directory and extract cross-table lineage."""
        all_edges: list[ColumnLineageEdge] = []
        for sql_file in models_dir.glob("*.sql"):
            table_name = sql_file.stem
            sql_text = sql_file.read_text(encoding="utf-8")
            edges = self.parse_query_lineage(table_name, sql_text)
            all_edges.extend(edges)
        return all_edges
