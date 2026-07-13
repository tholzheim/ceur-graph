"""
codegen: generate Pydantic models and FastAPI routers from the LinkML schema at import time.

All generated model classes are exposed as module-level attributes so they can be
imported directly:

    from wbforms.codegen import Paper, PaperCreate, SubjectBase
"""

from wbforms.codegen.fastapi_gen import generate_routers
from wbforms.codegen.pydantic_gen import generate_models
from wbforms.settings import get_settings

_SCHEMA_PATH = get_settings().schema_path

_models: dict = generate_models(_SCHEMA_PATH)

# Expose every generated class as a top-level attribute of this module.
globals().update(_models)

__all__ = list(_models.keys())


def get_models() -> dict:
    return _models


def get_routers():
    return generate_routers(_SCHEMA_PATH, _models)
