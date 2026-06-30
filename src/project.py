from .normalize import normalize_phone, normalize_skill

NORMALIZERS = {
    "E164": lambda v: normalize_phone(v) if v else v,
    "canonical": lambda v: normalize_skill(v) if isinstance(v, str) else v,
}

def _resolve_path(record: dict, from_path: str):
    
    if not isinstance(record, dict):
        return None

    if "[]." in from_path:
        list_key, sub_field = from_path.split("[].", 1)
        items = _resolve_path(record, list_key)
        if not isinstance(items, list):
            return None
        return [_resolve_path(item, sub_field) for item in items if isinstance(item, dict)]

    if "." in from_path:
        parts = from_path.split(".")
        curr = record
        for part in parts:
            if not isinstance(curr, dict):
                return None
            if "[" in part and part.endswith("]"):
                key, index_str = part[:-1].split("[")
                try:
                    index = int(index_str)
                except ValueError:
                    return None
                curr = curr.get(key, [])
                if not isinstance(curr, list) or index >= len(curr):
                    return None
                curr = curr[index]
            else:
                curr = curr.get(part)
        return curr

    if "[" in from_path and from_path.endswith("]"):
        key, index_str = from_path[:-1].split("[")
        try:
            index = int(index_str)
        except ValueError:
            return None
        items = record.get(key, [])
        if not isinstance(items, list) or index >= len(items):
            return None
        return items[index]

    return record.get(from_path)


def _apply_normalize(value, normalize_name: str | None):
    if not normalize_name or value is None:
        return value
    fn = NORMALIZERS.get(normalize_name)
    if not fn:
        return value                                                        
    if isinstance(value, list):
        return [fn(v) for v in value]
    return fn(value)


def _set_nested(output: dict, path: str, value):
    """Sets output[path] = value, supporting one level of dot-nesting (e.g. 'contact.email')."""
    if "." in path:
        top, rest = path.split(".", 1)
        output.setdefault(top, {})
        output[top][rest] = value
    else:
        output[path] = value


def project(canonical: dict, config: dict | None) -> dict:
    """
    Applies a runtime config to a canonical record. If config is None,
    returns the canonical record unchanged (the default schema case).
    """
    if config is None:
        return canonical

    include_confidence = config.get("include_confidence", True)
    on_missing = config.get("on_missing", "null")                             
    output = {}

    for field_spec in config.get("fields", []):
        out_path = field_spec.get("path", field_spec.get("from"))
        from_path = field_spec.get("from", field_spec.get("path"))
        normalize_name = field_spec.get("normalize")
        required = field_spec.get("required", False)

        value = _resolve_path(canonical, from_path)
        value = _apply_normalize(value, normalize_name)

        is_missing = value is None or value == [] or value == ""
        if is_missing:
            if on_missing == "error" and required:
                raise ValueError(f"required field '{out_path}' is missing")
            if on_missing == "omit":
                continue
            value = None                           

        _set_nested(output, out_path, value)

    if include_confidence and "overall_confidence" in canonical:
        output["overall_confidence"] = canonical["overall_confidence"]
    if config.get("include_provenance", include_confidence) and "provenance" in canonical:
        output["provenance"] = canonical["provenance"]

    return output