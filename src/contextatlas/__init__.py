"""ContextAtlas: Governed Metadata Enrichment and Catalog Navigation Engine for AI Agents.

Alias namespace providing backward compatibility with cforge.
"""

import sys
import cforge

# Re-export all submodules
from cforge import *
from cforge import config, llm, estate, catalog, lineage, enrichment, quality, governance, mcp, eval, adapters, api

__version__ = "0.1.0"
