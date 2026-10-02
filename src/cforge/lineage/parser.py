"""Column-Level Lineage Parser using sqlglot AST traversal.

Extracts column-to-column dependencies across SQL queries, CTEs, and table joins.
"""

from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional, Any
import sqlglot
from sqlglot import exp, parse_one
from sqlglot.lineage import lineage


class ColumnLineageEdge:
    def __init__(self, source_table: str, source_column: str,
                 target_table: str, target_column: str,
                 transformation_type: str = "DIRECT_COPY",
                 expression: Optional[str] = None):
        self.source_table = source_table
        self.source_column = source_column
        self.target_table = target_table
        self.target_column = target_column
        self.transformation_type = transformation_type
        self.expression = expression

    def to_dict(self) -> Dict[str, Any]:
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

    def parse_query_lineage(self, target_table_name: str, sql_text: str) -> List[ColumnLineageEdge]:
        """Parse a SQL query and extract all column lineage edges targeting target_table_name."""
        edges: List[ColumnLineageEdge] = []
        try:
            tree = parse_one(sql_text, read=self.dialect)
        except Exception:
            return edges

        # Extract table aliases in FROM and JOINs
        table_aliases: Dict[str, str] = {}
        for table in tree.find_all(exp.Table):
            t_name = table.name
            t_alias = table.alias_or_name
            if t_alias and t_name:
                table_aliases[t_alias] = t_name

        # Extract CTE names
        ctes: Dict[str, exp.CTE] = {}
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

            # Use sqlglot lineage tool first
            try:
                node = lineage(col_alias, sql_text, dialect=self.dialect)
                sources = set()
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

                for s_tbl, s_col in sources:
                    edges.append(ColumnLineageEdge(
                        source_table=s_tbl,
                        source_column=s_col,
                        target_table=target_table_name,
                        target_column=col_alias,
                        transformation_type=tx_type,
                        expression=expr.sql()
                    ))
            except Exception:
                # Fallback to direct AST column traversal
                cols_in_expr = list(expr.find_all(exp.Column))
                for col_node in cols_in_expr:
                    col_name = col_node.name
                    tbl_alias = col_node.table or ""
                    real_tbl = table_aliases.get(tbl_alias, tbl_alias or (list(table_aliases.values())[0] if table_aliases else "source"))
                    edges.append(ColumnLineageEdge(
                        source_table=real_tbl,
                        source_column=col_name,
                        target_table=target_table_name,
                        target_column=col_alias,
                        transformation_type=tx_type,
                        expression=expr.sql()
                    ))

        return edges

    def parse_models_directory(self, models_dir: Path) -> List[ColumnLineageEdge]:
        """Parse all .sql files in the models directory and extract cross-table lineage."""
        all_edges: List[ColumnLineageEdge] = []
        for sql_file in models_dir.glob("*.sql"):
            table_name = sql_file.stem
            sql_text = sql_file.read_text(encoding="utf-8")
            edges = self.parse_query_lineage(table_name, sql_text)
            all_edges.extend(edges)
        return all_edges
