"""Session-aware storage and persistence for pracovné údaje (work estimates)."""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Iterable, List, Sequence

from helpers import parse_float, secure_load_json, secure_save_json

# Ordered fields for export to Excel or archiving
PRACA_EXPORT_COLUMNS = (
    "rola",
    "osoby",
    "hodiny",
    "plat",
    "spolu",
    "koeficient",
    "predaj",
)

# In-memory snapshot of the currently edited project
current_praca: list[dict[str, Any]] = []


def _sanitize_int(value: Any, default: str = "0") -> str:
    """Return a non-negative integer stored as string."""
    try:
        number = int(round(parse_float(str(value))))
        if number < 0:
            number = 0
        return str(number)
    except Exception:
        return default


def _sanitize_float(value: Any, default: float = 0.0, decimals: int = 2) -> str:
    """Return a float formatted to the requested precision."""
    try:
        number = parse_float(str(value))
    except Exception:
        number = default
    if number < 0 and default >= 0:
        number = default
    fmt = f"{{:.{decimals}f}}"
    return fmt.format(number)


def normalize_praca_row(row: Any) -> dict[str, Any]:
    """Normalize a single praca row to the expected dict structure."""

    if isinstance(row, dict):
        data = dict(row)
    elif isinstance(row, (list, tuple)):
        values: List[Any] = list(row)
        # Ensure we have at least len(PRACA_EXPORT_COLUMNS) slots
        while len(values) < len(PRACA_EXPORT_COLUMNS):
            values.append("")
        data = {
            "rola": values[0],
            "osoby": values[1],
            "hodiny": values[2],
            "plat": values[3],
            "spolu": values[4],
            "koeficient": values[5],
            "predaj": values[6],
        }
        if len(values) > 7:
            data["pay_editable"] = values[7]
        if len(values) > 8:
            data["role_id"] = values[8]
    else:
        data = {}

    rola = str(data.get("rola", "") or "")
    osoby = _sanitize_int(data.get("osoby", "1"), default="1")
    hodiny = _sanitize_int(data.get("hodiny", "8"), default="0")
    plat = _sanitize_float(data.get("plat", "0"), default=0.0)
    koef = _sanitize_float(data.get("koeficient", "1"), default=1.0)

    # Calculate derived values
    try:
        spolu_val = int(osoby) * int(hodiny) * parse_float(plat)
    except Exception:
        spolu_val = 0.0
    spolu = _sanitize_float(spolu_val, default=0.0)

    try:
        predaj_val = parse_float(spolu) * parse_float(koef)
    except Exception:
        predaj_val = 0.0
    predaj = _sanitize_float(predaj_val, default=0.0)

    pay_editable = bool(data.get("pay_editable", True))
    role_id = str(data.get("role_id") or "").strip()

    return {
        "rola": rola,
        "osoby": osoby,
        "hodiny": hodiny,
        "plat": plat,
        "spolu": spolu,
        "koeficient": koef,
        "predaj": predaj,
        "pay_editable": pay_editable,
        "role_id": role_id,
    }


def normalize_praca_data(data: Any) -> list[dict[str, Any]]:
    """Normalize arbitrary praca payloads into a list of row dicts."""

    if not data:
        return []

    source: Iterable[Any]
    if isinstance(data, dict) and not all(k in data for k in PRACA_EXPORT_COLUMNS):
        # Support legacy wrappers like {"rows": [...]}
        if isinstance(data.get("rows"), Sequence):
            source = data.get("rows")  # type: ignore[assignment]
        else:
            source = [data]
    elif isinstance(data, Sequence) and not isinstance(data, (str, bytes)):
        source = data  # type: ignore[assignment]
    else:
        source = [data]

    normalized: list[dict[str, Any]] = []
    for row in source:
        normalized.append(normalize_praca_row(row))
    return normalized


def save_praca_data(rows: Any) -> list[dict[str, Any]]:
    """Store the provided rows in memory (normalized) and return a copy."""

    normalized = normalize_praca_data(rows)
    current_praca.clear()
    current_praca.extend(deepcopy(normalized))
    return deepcopy(current_praca)


def load_praca_from_project(commit_file: str) -> list[dict[str, Any]]:
    """Load praca rows from the given project JSON file."""

    data = secure_load_json(commit_file, default={})
    return normalize_praca_data(data.get("praca"))


def save_praca_to_project(commit_file: str, rows: Any) -> None:
    """Persist praca rows into the project JSON file."""

    data = secure_load_json(commit_file, default={})
    normalized = normalize_praca_data(rows)
    data["praca"] = normalized
    secure_save_json(commit_file, data)
    save_praca_data(normalized)


def rows_for_export(rows: Any | None = None) -> list[list[str]]:
    """Return rows formatted for Excel export (list of string lists)."""

    payload = rows if rows is not None else current_praca
    normalized = normalize_praca_data(payload)
    export_rows: list[list[str]] = []
    for row in normalized:
        export_rows.append([row.get(col, "") for col in PRACA_EXPORT_COLUMNS])
    return export_rows


def load_rows_for_export(commit_file: str) -> list[list[str]]:
    """Helper that loads praca rows from disk prepared for export."""

    return rows_for_export(load_praca_from_project(commit_file))

