"""Generate Pydantic models from a LinkML schema at runtime."""

from pathlib import Path
from typing import Any, get_origin

import yaml
from linkml_runtime.utils.schemaview import SchemaView
from pydantic import AnyHttpUrl, ConfigDict, Field, create_model
from wikibaseintegrator import datatypes
from wikibaseintegrator.wbi_enums import WikibaseSnakType

from ceur_graph.datamodel.item import (
    CEUR_DEV_ID,
    WIKIBASE_TYPE,
    WIKIDATA_ID,
    EntityBase,
    ExtractedStatement,
    ItemBase,
    ItemStatementSubjectType,
    Statement,
)
from ceur_graph.datamodel.utils import make_partial_model

RANGE_TO_PYTHON: dict[str, Any] = {
    "string": str,
    "integer": int,
    "anyuri": AnyHttpUrl,
    "item_statement_subject": ItemStatementSubjectType,
    "boolean": bool,
    "float": float,
    "uri": str,
}

WIKIBASE_DTYPE_MAP: dict[str, str] = {
    "item": datatypes.Item.DTYPE,
    "url": datatypes.URL.DTYPE,
    "monolingualtext": datatypes.MonolingualText.DTYPE,
    "string": datatypes.String.DTYPE,
    "external-id": datatypes.ExternalID.DTYPE,
    "quantity": datatypes.Quantity.DTYPE,
}

PYTHON_BASE_INFO: dict[str, tuple[type, type]] = {
    "entity_item": (EntityBase, ItemBase),
    "extracted_statement": (ExtractedStatement, Statement),
}


def _ann_dict(annotations) -> dict[str, str]:
    """Convert any annotation container (dict, JsonObj, …) to a plain {key: value_str} dict."""
    if not annotations:
        return {}
    result: dict[str, str] = {}
    try:
        if isinstance(annotations, dict):
            pairs = annotations.items()
        else:
            pairs = [(k, annotations[k]) for k in annotations]
        for k, v in pairs:
            result[str(k)] = v.value if hasattr(v, "value") else str(v)
    except Exception:
        pass
    return result


def _slot_annotations(view: SchemaView, slot_name: str, class_name: str, induced_slot) -> dict[str, str]:
    """Return merged annotations for a slot in a class, with slot_usage taking priority."""
    anns = _ann_dict(induced_slot.annotations)
    cls_def = view.get_class(class_name)
    if cls_def and cls_def.slot_usage and slot_name in cls_def.slot_usage:
        su = cls_def.slot_usage[slot_name]
        if su.annotations:
            anns.update(_ann_dict(su.annotations))
    return anns


def _is_statement_subject(anns: dict[str, str]) -> bool:
    val = anns.get("ceur_dev_id", "")
    parts = val.split("/")
    return len(parts) >= 2 and parts[-2] == "statement"


def _build_field_def(
    slot, anns: dict[str, str], is_required: bool, is_stmt_subject: bool, models: dict
) -> tuple[Any, Any]:
    """Return (python_type, FieldInfo) for a single slot."""
    range_name = slot.range or "string"

    # Check if range refers to a generated schema class (statement-reference field)
    if range_name in models and range_name not in RANGE_TO_PYTHON:
        stmt_cls = models[range_name]
        if slot.multivalued:
            return list[stmt_cls], Field(default_factory=list)
        else:
            return stmt_cls | None, Field(default=None)

    py_type: Any = RANGE_TO_PYTHON.get(range_name, str)

    if slot.multivalued:
        py_type = list[py_type]

    extra: dict[str, Any] = {}
    if ceur_dev_id := anns.get("ceur_dev_id"):
        extra[CEUR_DEV_ID] = ceur_dev_id
    if wd_id := anns.get("wikidata_id"):
        extra[WIKIDATA_ID] = wd_id
    if wb_type := anns.get("wikibase_type"):
        extra[WIKIBASE_TYPE] = WIKIBASE_DTYPE_MAP.get(wb_type, wb_type)

    field_kwargs: dict[str, Any] = {}
    if extra:
        field_kwargs["json_schema_extra"] = extra
    if slot.pattern:
        field_kwargs["pattern"] = slot.pattern

    if is_stmt_subject:
        default: Any = WikibaseSnakType.UNKNOWN_VALUE.value
        return py_type, Field(default=default, **field_kwargs)
    elif is_required:
        return py_type, Field(default=..., **field_kwargs)
    elif get_origin(py_type) is list:
        # Multivalued optional: keep as list[T] with empty-list default (not list[T] | None)
        return py_type, Field(default_factory=list, **field_kwargs)
    else:
        return py_type | None, Field(default=None, **field_kwargs)


def _topological_order(view: SchemaView) -> list[str]:
    """Return class names in dependency order (parents and slot-range classes before dependents)."""
    visited: set[str] = set()
    result: list[str] = []
    all_class_names: set[str] = set(view.all_classes().keys())

    def visit(name: str) -> None:
        if name in visited:
            return
        visited.add(name)
        cls = view.get_class(name)
        if cls is None:
            return
        if cls.is_a:
            visit(cls.is_a)
        # Treat slot ranges that are schema classes as dependencies
        for slot_name in (cls.slots or []):
            slot_def = view.get_slot(slot_name)
            if slot_def and slot_def.range in all_class_names:
                visit(slot_def.range)
        result.append(name)

    for name in view.all_classes():
        visit(name)
    return result


def generate_models(schema_path: Path) -> dict[str, type]:
    """Parse the LinkML schema and return a dict of generated Pydantic model classes."""
    raw = yaml.safe_load(schema_path.read_text(encoding="utf-8"))
    raw.pop("endpoints", None)
    view = SchemaView(yaml.dump(raw))
    models: dict[str, type] = {}

    for class_name in _topological_order(view):
        cls_def = view.get_class(class_name)
        if cls_def is None:
            continue

        python_base_key = _ann_dict(cls_def.annotations).get("python_base")
        parent_name = cls_def.is_a

        if python_base_key is None and parent_name:
            parent_def = view.get_class(parent_name)
            if parent_def:
                python_base_key = _ann_dict(parent_def.annotations).get("python_base")

        if python_base_key not in PYTHON_BASE_INFO:
            continue

        root_base_cls, read_extra_cls = PYTHON_BASE_INFO[python_base_key]

        if parent_name and f"{parent_name}Base" in models:
            base_cls = models[f"{parent_name}Base"]
        else:
            base_cls = root_base_cls

        own_slots: set[str] = set(cls_def.slots or [])
        overridden_slots: set[str] = set(cls_def.slot_usage.keys() if cls_def.slot_usage else [])
        slots_to_gen = own_slots | overridden_slots

        field_defs: dict[str, tuple[Any, Any]] = {}
        for slot_name in slots_to_gen:
            induced = view.induced_slot(slot_name, class_name)
            anns = _slot_annotations(view, slot_name, class_name, induced)
            is_req = bool(induced.required)
            is_stmt_subj = _is_statement_subject(anns)
            if is_stmt_subj:
                is_req = False

            py_type, field_info = _build_field_def(induced, anns, is_req, is_stmt_subj, models)
            field_defs[slot_name] = (py_type, field_info)

        model_title = _ann_dict(cls_def.annotations).get("model_title")
        _raw_enforce = _ann_dict(cls_def.annotations).get("enforce_unknown_stmt_name", False)
        enforce_stmt_name = _raw_enforce is True or (isinstance(_raw_enforce, str) and _raw_enforce.lower() == "true")
        if model_title or enforce_stmt_name:
            extra_attrs: dict = {"__module__": "ceur_graph.codegen"}
            if model_title:
                extra_attrs["model_config"] = ConfigDict(title=model_title)
            if enforce_stmt_name:
                extra_attrs["_enforce_unknown_stmt_name"] = True
            base_cls = type(f"_{class_name}Configured", (base_cls,), extra_attrs)

        base_model = create_model(
            f"{class_name}Base",
            __base__=base_cls,
            __module__="ceur_graph.codegen",
            **field_defs,
        )

        create_model_cls = create_model(
            f"{class_name}Create",
            __base__=base_model,
            __module__="ceur_graph.codegen",
        )

        update_model = make_partial_model(create_model_cls, f"{class_name}Update")

        read_model = type(class_name, (base_model, read_extra_cls), {"__module__": "ceur_graph.codegen"})

        models[f"{class_name}Base"] = base_model
        models[f"{class_name}Create"] = create_model_cls
        models[f"{class_name}Update"] = update_model
        models[class_name] = read_model

    return models
