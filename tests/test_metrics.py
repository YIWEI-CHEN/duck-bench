"""Tests for DUCK-Bench metric implementations."""

import sqlite3
import tempfile
from pathlib import Path

import pytest

from evaluation.metrics import (
    execute_sql,
    execution_accuracy,
    modality_coverage,
    schema_linking_f1,
    soft_f1,
    valid_efficiency_score,
)


@pytest.fixture
def sample_db(tmp_path):
    """Create a sample SQLite database for testing."""
    db_path = str(tmp_path / "test.db")
    conn = sqlite3.connect(db_path)
    conn.executescript("""
        CREATE TABLE accounts (
            id INTEGER PRIMARY KEY,
            name TEXT,
            region TEXT
        );
        CREATE TABLE opportunities (
            id INTEGER PRIMARY KEY,
            account_id INTEGER,
            amount REAL,
            status TEXT,
            FOREIGN KEY (account_id) REFERENCES accounts(id)
        );
        INSERT INTO accounts VALUES (1, 'Contoso', 'West');
        INSERT INTO accounts VALUES (2, 'Fabrikam', 'East');
        INSERT INTO accounts VALUES (3, 'Northwind', 'West');
        INSERT INTO opportunities VALUES (1, 1, 500000, 'closed-won');
        INSERT INTO opportunities VALUES (2, 1, 200000, 'open');
        INSERT INTO opportunities VALUES (3, 2, 750000, 'closed-won');
        INSERT INTO opportunities VALUES (4, 3, 100000, 'closed-lost');
    """)
    conn.close()
    return db_path


class TestExecuteSQL:
    def test_basic_query(self, sample_db):
        rows, elapsed = execute_sql(sample_db, "SELECT name FROM accounts ORDER BY name")
        assert rows == [("Contoso",), ("Fabrikam",), ("Northwind",)]
        assert elapsed >= 0

    def test_aggregate_query(self, sample_db):
        rows, _ = execute_sql(sample_db, "SELECT COUNT(*) FROM opportunities")
        assert rows == [(4,)]

    def test_invalid_sql(self, sample_db):
        with pytest.raises(sqlite3.OperationalError):
            execute_sql(sample_db, "SELECT * FROM nonexistent_table")


class TestExecutionAccuracy:
    def test_matching_queries(self, sample_db):
        sql1 = "SELECT name FROM accounts WHERE region = 'West'"
        sql2 = "SELECT name FROM accounts WHERE region = 'West'"
        assert execution_accuracy(sample_db, sql1, sql2) is True

    def test_equivalent_queries(self, sample_db):
        pred = "SELECT a.name FROM accounts a WHERE a.region = 'West' ORDER BY a.name"
        gold = "SELECT name FROM accounts WHERE region = 'West'"
        assert execution_accuracy(sample_db, pred, gold) is True

    def test_different_results(self, sample_db):
        pred = "SELECT name FROM accounts WHERE region = 'East'"
        gold = "SELECT name FROM accounts WHERE region = 'West'"
        assert execution_accuracy(sample_db, pred, gold) is False

    def test_invalid_pred_sql(self, sample_db):
        pred = "SELECT * FROM fake_table"
        gold = "SELECT name FROM accounts"
        assert execution_accuracy(sample_db, pred, gold) is False


class TestValidEfficiencyScore:
    def test_correct_query(self, sample_db):
        sql = "SELECT name FROM accounts WHERE region = 'West'"
        score = valid_efficiency_score(sample_db, sql, sql)
        assert 0.0 < score <= 1.0

    def test_incorrect_query(self, sample_db):
        pred = "SELECT name FROM accounts WHERE region = 'East'"
        gold = "SELECT name FROM accounts WHERE region = 'West'"
        assert valid_efficiency_score(sample_db, pred, gold) == 0.0

    def test_invalid_query(self, sample_db):
        pred = "INVALID SQL"
        gold = "SELECT name FROM accounts"
        assert valid_efficiency_score(sample_db, pred, gold) == 0.0


class TestModalityCoverage:
    def test_full_coverage_with_schema(self):
        schema = {"accounts": "crm", "audit_log": "log"}
        sql = "SELECT * FROM accounts JOIN audit_log ON accounts.id = audit_log.entity_id"
        assert modality_coverage(sql, ["crm", "log"], schema) == 1.0

    def test_partial_coverage_with_schema(self):
        schema = {"accounts": "crm", "audit_log": "log"}
        sql = "SELECT * FROM accounts"
        assert modality_coverage(sql, ["crm", "log"], schema) == 0.5

    def test_no_coverage(self):
        schema = {"accounts": "crm", "audit_log": "log"}
        sql = "SELECT 1"
        assert modality_coverage(sql, ["crm", "log"], schema) == 0.0

    def test_empty_modalities(self):
        assert modality_coverage("SELECT 1", []) == 1.0

    def test_keyword_heuristic_fallback(self):
        sql = "SELECT * FROM account_table JOIN meeting_notes ON 1=1"
        score = modality_coverage(sql, ["crm", "meeting_recap"])
        assert score > 0.0


class TestSchemaLinkingF1:
    def test_identical_queries(self):
        sql = "SELECT name, region FROM accounts WHERE region = 'West'"
        result = schema_linking_f1(sql, sql)
        assert result["table_f1"] == 1.0
        assert result["f1"] > 0.0

    def test_different_tables(self):
        pred = "SELECT name FROM accounts"
        gold = "SELECT name FROM opportunities"
        result = schema_linking_f1(pred, gold)
        assert result["table_f1"] == 0.0

    def test_partial_overlap(self):
        pred = "SELECT name FROM accounts JOIN opportunities ON accounts.id = opportunities.account_id"
        gold = "SELECT name FROM accounts"
        result = schema_linking_f1(pred, gold)
        assert result["table_recall"] == 1.0
        assert result["table_precision"] == 0.5

    def test_empty_queries(self):
        result = schema_linking_f1("", "")
        assert result["table_f1"] == 1.0


class TestSoftF1:
    def test_identical_text(self):
        result = soft_f1("hello world", "hello world")
        assert result["f1"] == 1.0

    def test_partial_overlap(self):
        result = soft_f1("hello world foo", "hello world bar")
        assert 0.0 < result["f1"] < 1.0
        assert result["precision"] == pytest.approx(2 / 3)
        assert result["recall"] == pytest.approx(2 / 3)

    def test_no_overlap(self):
        result = soft_f1("foo bar", "baz qux")
        assert result["f1"] == 0.0

    def test_empty_both(self):
        result = soft_f1("", "")
        assert result["f1"] == 1.0

    def test_empty_pred(self):
        result = soft_f1("", "hello world")
        assert result["f1"] == 0.0

    def test_case_insensitive(self):
        result = soft_f1("Hello World", "hello world")
        assert result["f1"] == 1.0
