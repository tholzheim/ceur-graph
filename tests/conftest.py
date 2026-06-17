"""Pin the test suite to the bundled ceur_graph.yaml schema.

Codegen (ceur_graph.codegen) builds all Pydantic models at import time from
get_settings().schema_path. A developer's local .env may repoint that at an
alternative schema (e.g. factgrid_besucherbuch.yaml), which would strip the
ceur_graph classes the tests rely on. We force the canonical schema here,
before any test module imports codegen.
"""

import os
from pathlib import Path

_SCHEMA = Path(__file__).resolve().parent.parent / "src" / "ceur_graph" / "schema" / "ceur_graph.yaml"
os.environ["WBFORMS_SCHEMA_PATH"] = str(_SCHEMA)

# Defensive: drop any settings cached before this override took effect.
from ceur_graph.settings import get_settings  # noqa: E402

get_settings.cache_clear()
