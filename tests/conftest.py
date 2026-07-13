"""Pin the test suite to the bundled ceur_graph.yaml schema.

Codegen (wbforms.codegen) builds all Pydantic models at import time from
get_settings().schema_path. A developer's local .env may repoint that at an
alternative schema (e.g. factgrid_besucherbuch.yaml), which would strip the
wbforms classes the tests rely on. We force the canonical schema here,
before any test module imports codegen.
"""

import os
from pathlib import Path

_SCHEMA = Path(__file__).resolve().parent.parent / "src" / "wbforms" / "schema" / "ceur_graph.yaml"
os.environ["WBFORMS_SCHEMA_PATH"] = str(_SCHEMA)

# Defensive: drop any settings cached before this override took effect.
from wbforms.settings import get_settings  # noqa: E402

get_settings.cache_clear()
