
import pytest
import sys
from pathlib import Path
import pathlib
sys.path.append(
        str(pathlib.Path(__file__).resolve().parent.parent)  
)
from guardrails.sql_validator import validate_sql


# ======================================
# VALID SQL
# ======================================

def test_allow_simple_select():

    sql = """
    SELECT *
    FROM matches
    LIMIT 10
    """

    assert validate_sql(sql) is True


def test_allow_cte_query():

    sql = """
    WITH wickets AS (
        SELECT bowler,
               COUNT(*) AS total_wickets
        FROM deliveries
        GROUP BY bowler
    )
    SELECT *
    FROM wickets
    """

    assert validate_sql(sql) is True


def test_allow_lowercase_select():

    sql = """
    select *
    from matches
    """

    assert validate_sql(sql) is True


# ======================================
# EMPTY SQL
# ======================================

def test_reject_empty_sql():

    with pytest.raises(
        ValueError,
        match="Empty SQL query generated"
    ):
        validate_sql("")


# ======================================
# BLOCKED COMMANDS
# ======================================

def test_block_drop():

    sql = """
    DROP TABLE matches
    """

    with pytest.raises(
        ValueError,
        match="Blocked SQL command"
    ):
        validate_sql(sql)


def test_block_delete():

    sql = """
    DELETE FROM deliveries
    """

    with pytest.raises(
        ValueError,
        match="Blocked SQL command"
    ):
        validate_sql(sql)


def test_block_update():

    sql = """
    UPDATE matches
    SET city = 'Mumbai'
    """

    with pytest.raises(
        ValueError,
        match="Blocked SQL command"
    ):
        validate_sql(sql)


def test_block_insert():

    sql = """
    INSERT INTO matches
    VALUES (1)
    """

    with pytest.raises(
        ValueError,
        match="Blocked SQL command"
    ):
        validate_sql(sql)


# ======================================
# FIRST STATEMENT CHECK
# ======================================

def test_only_select_or_with_allowed():

    sql = """
    SHOW TABLES
    """

    with pytest.raises(
        ValueError,
        match="Only SELECT and WITH statements"
    ):
        validate_sql(sql)


# ======================================
# MULTIPLE STATEMENTS
# ======================================

def test_block_multiple_statements():

    sql = """
    SELECT *
    FROM matches;

    DROP TABLE matches;
    """

    with pytest.raises(ValueError):
        validate_sql(sql)


# ======================================
# CASE INSENSITIVE
# ======================================

def test_block_lowercase_delete():

    sql = """
    delete from deliveries
    """

    with pytest.raises(
        ValueError
    ):
        validate_sql(sql)


def test_block_mixed_case_drop():

    sql = """
    DrOp Table matches
    """

    with pytest.raises(
        ValueError
    ):
        validate_sql(sql)