"""Derive REST endpoint definitions from the classes of the LinkML schema.

Endpoints are not declared in the schema; they are derived from the classes:

- Every class with ``python_base: entity_item`` gets an item endpoint at
  ``/<classname lowercased>`` with path parameter ``<classname lowercased>_id``.
- Every statement-reference slot on such a class (a slot whose range is an
  ``extracted_statement`` class) mounts a statement endpoint at
  ``<item prefix>/{<id_param>}/<slot name>``. Inherited slots count, so a subclass
  automatically gets its own statement routes.

Optional annotations override the conventions:

- class level (item): ``endpoint_prefix``, ``endpoint_tag``, ``generate_endpoint: false``
- class level (statement): ``endpoint_tag``, ``has_get_by_id``, ``has_delete_by_object``
  (inherited via ``is_a`` when not set on the class itself)
- slot level: ``endpoint_segment`` (path segment, defaults to the slot name)
"""

from functools import lru_cache
from pathlib import Path

import yaml
from linkml_runtime.utils.schemaview import SchemaView

from wbforms.codegen.pydantic_gen import _ann_dict, _slot_annotations, _truthy

ENTITY_ITEM = "entity_item"
EXTRACTED_STATEMENT = "extracted_statement"


def _python_base(view: SchemaView, cls) -> str | None:
    """Resolve the python_base annotation of a class, walking the is_a chain."""
    seen: set[str] = set()
    while cls is not None and cls.name not in seen:
        seen.add(cls.name)
        base = _ann_dict(cls.annotations).get("python_base")
        if base:
            return base
        cls = view.get_class(cls.is_a) if cls.is_a else None
    return None


def _inherited_class_annotation(view: SchemaView, cls, key: str) -> str | None:
    """Return a class annotation value, falling back to is_a ancestors."""
    seen: set[str] = set()
    while cls is not None and cls.name not in seen:
        seen.add(cls.name)
        value = _ann_dict(cls.annotations).get(key)
        if value is not None:
            return value
        cls = view.get_class(cls.is_a) if cls.is_a else None
    return None


@lru_cache(maxsize=4)
def derive_endpoints(schema_path: Path) -> list[dict]:
    """Return the endpoint definitions (item and statement) derived from the schema."""
    raw = yaml.safe_load(schema_path.read_text(encoding="utf-8"))
    raw.pop("endpoints", None)  # legacy explicit sections are ignored
    view = SchemaView(yaml.dump(raw))
    all_class_names = set(view.all_classes().keys())

    endpoints: list[dict] = []
    for class_name in view.all_classes():
        cls = view.get_class(class_name)
        if cls is None or _python_base(view, cls) != ENTITY_ITEM:
            continue
        anns = _ann_dict(cls.annotations)
        if str(anns.get("generate_endpoint", "true")).lower() == "false":
            continue

        id_param = f"{class_name.lower()}_id"
        prefix = anns.get("endpoint_prefix") or f"/{class_name.lower()}"
        endpoints.append(
            {
                "model": class_name,
                "type": "item",
                "prefix": prefix,
                "tag": anns.get("endpoint_tag") or class_name,
                "id_param": id_param,
            }
        )

        for slot_name in view.class_slots(class_name):
            induced = view.induced_slot(slot_name, class_name)
            if induced.range not in all_class_names:
                continue
            stmt_cls = view.get_class(induced.range)
            if _python_base(view, stmt_cls) != EXTRACTED_STATEMENT:
                continue
            slot_anns = _slot_annotations(view, slot_name, class_name, induced)
            segment = slot_anns.get("endpoint_segment") or slot_name
            endpoints.append(
                {
                    "model": induced.range,
                    "type": "statement",
                    "prefix": f"{prefix}/{{{id_param}}}/{segment}",
                    "tag": _inherited_class_annotation(view, stmt_cls, "endpoint_tag") or f"{class_name} {segment}",
                    "parent_param": id_param,
                    "has_get_by_id": _truthy(_inherited_class_annotation(view, stmt_cls, "has_get_by_id")),
                    "has_delete_by_object": _truthy(
                        _inherited_class_annotation(view, stmt_cls, "has_delete_by_object")
                    ),
                    # linkage used by the form-metadata builder
                    "parent_model": class_name,
                    "slot": slot_name,
                }
            )

    return endpoints
