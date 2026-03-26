"""DUCK-Bench Metric Implementations.

Metrics:
  - Execution Accuracy (EX): Does the predicted SQL return the correct result set?
  - Valid Efficiency Score (VES): Execution accuracy weighted by query efficiency.
  - Modality Coverage (MC): Fraction of required data modalities correctly accessed.
  - Schema Linking F1: Precision/recall of table and column references.
  - Soft F1: Token-level F1 for free-text extraction tasks.
"""

import re
import sqlite3
import time
from collections import Counter
from pathlib import Path


def execute_sql(db_path: str, sql: str, timeout: float = 30.0) -> tuple[list, float]:
    """Execute SQL against a SQLite database and return (results, execution_time).

    Args:
        db_path: Path to the SQLite database file.
        sql: SQL query string to execute.
        timeout: Maximum execution time in seconds.

    Returns:
        Tuple of (sorted result rows, execution time in seconds).

    Raises:
        sqlite3.Error: If the query fails.
        TimeoutError: If the query exceeds the timeout.
    """
    conn = sqlite3.connect(db_path)
    conn.execute(f"PRAGMA busy_timeout = {int(timeout * 1000)}")
    cursor = conn.cursor()
    start = time.perf_counter()
    cursor.execute(sql)
    rows = cursor.fetchall()
    elapsed = time.perf_counter() - start
    conn.close()
    if elapsed > timeout:
        raise TimeoutError(f"Query exceeded {timeout}s timeout")
    rows = [tuple(row) for row in rows]
    return sorted(rows), elapsed


def execution_accuracy(db_path: str, pred_sql: str, gold_sql: str) -> bool:
    """Execution Accuracy (EX): whether predicted SQL returns the same result set as gold.

    Args:
        db_path: Path to the SQLite database file.
        pred_sql: Predicted SQL query.
        gold_sql: Gold-standard SQL query.

    Returns:
        True if result sets match exactly.
    """
    try:
        pred_rows, _ = execute_sql(db_path, pred_sql)
        gold_rows, _ = execute_sql(db_path, gold_sql)
        return pred_rows == gold_rows
    except Exception:
        return False


def valid_efficiency_score(db_path: str, pred_sql: str, gold_sql: str) -> float:
    """Valid Efficiency Score (VES): EX weighted by relative query efficiency.

    VES = EX * sqrt(gold_time / pred_time), capped at 1.0.
    If the predicted SQL is incorrect, VES = 0.

    Args:
        db_path: Path to the SQLite database file.
        pred_sql: Predicted SQL query.
        gold_sql: Gold-standard SQL query.

    Returns:
        Score in [0.0, 1.0].
    """
    try:
        pred_rows, pred_time = execute_sql(db_path, pred_sql)
        gold_rows, gold_time = execute_sql(db_path, gold_sql)
        if pred_rows != gold_rows:
            return 0.0
        if pred_time == 0:
            return 1.0
        return min(1.0, (gold_time / pred_time) ** 0.5)
    except Exception:
        return 0.0


def modality_coverage(pred_sql: str, gold_modalities: list[str], schema: dict[str, str] | None = None) -> float:
    """Modality Coverage (MC): fraction of required data modalities accessed by the predicted SQL.

    Determines which modalities are referenced by checking table names in the SQL
    against a schema mapping of table -> modality. If no schema is provided, falls
    back to keyword heuristics.

    Args:
        pred_sql: Predicted SQL query.
        gold_modalities: List of required modalities from the gold question.
        schema: Optional dict mapping table names to their modality type.

    Returns:
        Coverage ratio in [0.0, 1.0].
    """
    if not gold_modalities:
        return 1.0

    pred_sql_lower = pred_sql.lower()

    if schema:
        pred_modalities = set()
        for table, modality in schema.items():
            if table.lower() in pred_sql_lower:
                pred_modalities.add(modality)
    else:
        modality_keywords = {
            "relational": ["select", "join", "where"],
            "crm": ["account", "contact", "lead", "opportunity", "case"],
            "log": ["log", "audit", "event", "history"],
            "file": ["attachment", "annotation", "document", "file"],
            "meeting_recap": ["meeting", "recap", "transcript", "call"],
            "multi_line_text": ["note", "description", "body", "comment"],
        }
        pred_modalities = set()
        for modality, keywords in modality_keywords.items():
            if any(kw in pred_sql_lower for kw in keywords):
                pred_modalities.add(modality)

    covered = sum(1 for m in gold_modalities if m in pred_modalities)
    return covered / len(gold_modalities)


def _extract_schema_refs(sql: str) -> tuple[set[str], set[str]]:
    """Extract table and column references from a SQL query.

    Uses simple regex-based extraction for FROM, JOIN, and SELECT clauses.

    Returns:
        Tuple of (table_names, column_names) as lowercase sets.
    """
    sql_clean = re.sub(r"--.*$", "", sql, flags=re.MULTILINE)
    sql_clean = re.sub(r"/\*.*?\*/", "", sql_clean, flags=re.DOTALL)

    tables = set()
    for match in re.finditer(r"\b(?:FROM|JOIN)\s+(\w+)", sql_clean, re.IGNORECASE):
        tables.add(match.group(1).lower())

    columns = set()
    for match in re.finditer(r"\b(?:\w+\.)?(\w+)\s*(?:=|<|>|!=|<=|>=|LIKE|IN|IS|BETWEEN|,)", sql_clean, re.IGNORECASE):
        col = match.group(1).lower()
        if col not in tables and col not in {"select", "from", "where", "and", "or", "not", "null", "true", "false"}:
            columns.add(col)

    for match in re.finditer(r"SELECT\s+(.*?)\s+FROM", sql_clean, re.IGNORECASE | re.DOTALL):
        for col_match in re.finditer(r"\b(?:\w+\.)?(\w+)\b", match.group(1)):
            col = col_match.group(1).lower()
            if col not in {"select", "distinct", "as", "case", "when", "then", "else", "end", "count", "sum", "avg", "min", "max"}:
                columns.add(col)

    return tables, columns


def schema_linking_f1(pred_sql: str, gold_sql: str) -> dict[str, float]:
    """Schema Linking F1: precision/recall of table and column references.

    Args:
        pred_sql: Predicted SQL query.
        gold_sql: Gold-standard SQL query.

    Returns:
        Dict with keys: table_precision, table_recall, table_f1,
        column_precision, column_recall, column_f1, f1 (average of both).
    """
    pred_tables, pred_cols = _extract_schema_refs(pred_sql)
    gold_tables, gold_cols = _extract_schema_refs(gold_sql)

    def _f1(pred_set: set, gold_set: set) -> tuple[float, float, float]:
        if not pred_set and not gold_set:
            return 1.0, 1.0, 1.0
        if not pred_set or not gold_set:
            return 0.0, 0.0, 0.0
        tp = len(pred_set & gold_set)
        precision = tp / len(pred_set) if pred_set else 0.0
        recall = tp / len(gold_set) if gold_set else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
        return precision, recall, f1

    tp, tr, tf = _f1(pred_tables, gold_tables)
    cp, cr, cf = _f1(pred_cols, gold_cols)

    return {
        "table_precision": tp,
        "table_recall": tr,
        "table_f1": tf,
        "column_precision": cp,
        "column_recall": cr,
        "column_f1": cf,
        "f1": (tf + cf) / 2,
    }


def soft_f1(pred_text: str, gold_text: str) -> dict[str, float]:
    """Soft F1: token-level F1 for free-text extraction tasks.

    Tokenizes by whitespace and lowercasing, then computes precision, recall, and F1
    based on token overlap counts.

    Args:
        pred_text: Predicted text output.
        gold_text: Gold-standard text output.

    Returns:
        Dict with keys: precision, recall, f1.
    """
    pred_tokens = Counter(pred_text.lower().split())
    gold_tokens = Counter(gold_text.lower().split())

    if not pred_tokens and not gold_tokens:
        return {"precision": 1.0, "recall": 1.0, "f1": 1.0}
    if not pred_tokens or not gold_tokens:
        return {"precision": 0.0, "recall": 0.0, "f1": 0.0}

    overlap = sum((pred_tokens & gold_tokens).values())
    precision = overlap / sum(pred_tokens.values())
    recall = overlap / sum(gold_tokens.values())
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

    return {"precision": precision, "recall": recall, "f1": f1}


METRICS = {
    "ex": execution_accuracy,
    "ves": valid_efficiency_score,
    "mc": modality_coverage,
    "schema_f1": schema_linking_f1,
    "soft_f1": soft_f1,
}
