"""Frontend routes: schema metadata endpoint, entity-search proxy, and SPA shell."""

from pathlib import Path
from typing import Any

import httpx
import yaml
from fastapi import APIRouter, Query
from fastapi.responses import FileResponse

from ceur_graph.codegen import get_models
from ceur_graph.datamodel.item import CEUR_DEV_ID, WIKIBASE_TYPE, StatementBase
from ceur_graph.wbgenerator import _is_list_annotation, get_statement_field_type

_SCHEMA_PATH = Path(__file__).parent.parent / "schema" / "ceur_graph.yaml"
_STATIC_DIR = Path(__file__).parent.parent / "static"

router = APIRouter()

_SKIP_FIELDS = {"qid", "statement_id"}
_INTERNAL_WB_IDS = {"rdf:subject", "rdfs:label", "schema:description"}


def _wikibase_type(field_info) -> str | None:
    extra = field_info.json_schema_extra
    if not isinstance(extra, dict):
        return None
    return extra.get(WIKIBASE_TYPE)


def _is_required(field_info) -> bool:
    from pydantic_core import PydanticUndefinedType
    return not isinstance(field_info.default, PydanticUndefinedType) and field_info.default is ... or (
        field_info.default is ... and field_info.default_factory is None
    )


def _label(name: str) -> str:
    return name.replace("_", " ").title()


def _build_statement_fields(stmt_cls: type) -> list[dict]:
    subject_field_name = stmt_cls.get_statement_subject(CEUR_DEV_ID)
    fields = []
    for fname, finfo in stmt_cls.model_fields.items():
        if fname in _SKIP_FIELDS:
            continue
        extra = finfo.json_schema_extra if isinstance(finfo.json_schema_extra, dict) else {}
        ceur_id = extra.get(CEUR_DEV_ID, "")
        if ceur_id in _INTERNAL_WB_IDS:
            continue
        entry = {
            "name": fname,
            "label": _label(fname),
            "wikibase_type": _wikibase_type(finfo),
            "field_type": "list" if _is_list_annotation(finfo.annotation) else "single",
            "required": finfo.is_required(),
        }
        if fname == subject_field_name:
            entry["is_subject"] = True
        if fname == "object_named_as":
            entry["is_object_named_as"] = True
        fields.append(entry)
    return fields


def _build_entity_schema(
    entity_name: str,
    model_cls: type,
    all_models: dict,
    endpoints: list[dict],
) -> dict:
    fields: list[dict] = []

    # Always expose label and description as top-level text inputs
    for meta_name, meta_label in [("label", "Label"), ("description", "Description")]:
        if meta_name in model_cls.model_fields:
            fields.append({
                "name": meta_name,
                "label": meta_label,
                "field_type": "single",
                "wikibase_type": "string",
                "required": True,
            })

    for fname, finfo in model_cls.model_fields.items():
        if fname in _SKIP_FIELDS or fname in {"label", "description"}:
            continue

        extra = finfo.json_schema_extra if isinstance(finfo.json_schema_extra, dict) else {}
        ceur_id = extra.get(CEUR_DEV_ID, "")
        if ceur_id in _INTERNAL_WB_IDS:
            continue

        # Statement-reference field (list[ScholarSignature], etc.)
        stmt_type = get_statement_field_type(finfo.annotation)
        if stmt_type is not None:
            stmt_name = stmt_type.__name__
            # Find matching endpoint
            stmt_endpoint = next(
                (ep for ep in endpoints if ep.get("model") == stmt_name and ep.get("type") == "statement"
                 and ep.get("parent_param", "").startswith(entity_name[0].lower())),
                None,
            )
            fields.append({
                "name": fname,
                "label": _label(fname),
                "field_type": "statement_list",
                "statement_model": stmt_name,
                "statement_endpoint": stmt_endpoint["prefix"] if stmt_endpoint else None,
                "statement_fields": _build_statement_fields(stmt_type),
                "enforce_unknown_stmt_name": bool(getattr(stmt_type, "_enforce_unknown_stmt_name", False)),
            })
            continue

        if not ceur_id or ceur_id in _INTERNAL_WB_IDS:
            continue

        fields.append({
            "name": fname,
            "label": _label(fname),
            "field_type": "list" if _is_list_annotation(finfo.annotation) else "single",
            "wikibase_type": _wikibase_type(finfo),
            "required": finfo.is_required(),
        })

    return {"name": entity_name, "fields": fields}


@router.get("/api/schema/entities")
def get_schema_entities() -> list[dict]:
    """Return schema metadata for all item-type entities, suitable for form generation."""
    raw = yaml.safe_load(_SCHEMA_PATH.read_text(encoding="utf-8"))
    endpoints: list[dict] = raw.get("endpoints", [])

    item_endpoints = [ep for ep in endpoints if ep.get("type") == "item"]
    all_models = get_models()

    result = []
    for ep in item_endpoints:
        model_name: str = ep["model"]
        model_cls = all_models.get(model_name)
        if model_cls is None:
            continue
        entity = _build_entity_schema(model_name, model_cls, all_models, endpoints)
        entity["endpoint_prefix"] = ep["prefix"]
        entity["id_param"] = ep.get("id_param", "item_id")
        result.append(entity)

    return result


@router.get("/api/entity-search")
async def entity_search(q: str = Query(..., min_length=1), limit: int = 10) -> list[dict]:
    """Proxy to wbsearchentities to avoid CORS issues from the browser."""
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            "https://ceur-dev.wikibase.cloud/w/api.php",
            params={
                "action": "wbsearchentities",
                "search": q,
                "language": "en",
                "type": "item",
                "format": "json",
                "limit": limit,
            },
            timeout=10.0,
        )
        resp.raise_for_status()
    return [
        {
            "id": r["id"],
            "label": r.get("label", r["id"]),
            "description": r.get("description", ""),
        }
        for r in resp.json().get("search", [])
    ]


@router.get("/api/entity-label")
async def entity_label(qid: str = Query(...), language: str = "en") -> dict:
    """Resolve a single QID to its label and description via wbgetentities."""
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            "https://ceur-dev.wikibase.cloud/w/api.php",
            params={
                "action": "wbgetentities",
                "ids": qid,
                "props": "labels|descriptions",
                "languages": language,
                "format": "json",
            },
            timeout=10.0,
        )
        resp.raise_for_status()
    entities = resp.json().get("entities", {})
    entity = entities.get(qid, {})
    label = entity.get("labels", {}).get(language, {}).get("value", qid)
    description = entity.get("descriptions", {}).get(language, {}).get("value", "")
    return {"qid": qid, "label": label, "description": description}


@router.get("/")
def serve_index() -> FileResponse:
    return FileResponse(_STATIC_DIR / "index.html")
