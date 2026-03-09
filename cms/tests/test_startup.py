"""
Startup and configuration regression tests.

Covers ordering and environment-loading invariants that are easy to break
during refactoring but don't surface as obvious runtime errors in CI (because
CI sets env vars directly, masking the bug).
"""
import ast
from pathlib import Path

MAIN_PY = Path(__file__).parent.parent / "app" / "main.py"


def _statements(source: str) -> list:
    """Return top-level AST statements from source."""
    return ast.parse(source).body


def _is_load_dotenv_call(node) -> bool:
    """True if the node is a bare `load_dotenv()` call statement."""
    return (
        isinstance(node, ast.Expr)
        and isinstance(node.value, ast.Call)
        and isinstance(node.value.func, ast.Name)
        and node.value.func.id == "load_dotenv"
    )


def _is_local_import(node) -> bool:
    """True if the node is a relative import (from .x import y)."""
    return isinstance(node, ast.ImportFrom) and node.level and node.level > 0


def test_load_dotenv_called_before_local_app_imports():
    """
    Regression: load_dotenv() must execute before any relative app imports so
    that module-level os.getenv() calls in db.py (e.g. ENDPOINT) read the
    correct values from .env rather than falling through to ~/.aws/credentials.

    If this test fails it means load_dotenv() has been moved below a local
    import and the app will silently use real AWS credentials in local dev.
    """
    source = MAIN_PY.read_text()
    stmts = _statements(source)

    load_dotenv_line = None
    first_local_import_line = None

    for node in stmts:
        if _is_load_dotenv_call(node) and load_dotenv_line is None:
            load_dotenv_line = node.lineno
        if _is_local_import(node) and first_local_import_line is None:
            first_local_import_line = node.lineno

    assert load_dotenv_line is not None, (
        "load_dotenv() call not found in main.py"
    )
    assert first_local_import_line is not None, (
        "No relative imports found in main.py — test may need updating"
    )
    assert load_dotenv_line < first_local_import_line, (
        f"load_dotenv() is on line {load_dotenv_line} but the first relative "
        f"import is on line {first_local_import_line}. "
        "load_dotenv() must come first so db.py reads DYNAMODB_ENDPOINT from "
        ".env before boto3 falls back to ~/.aws/credentials."
    )


def test_db_endpoint_env_var_read_at_module_level():
    """
    Documents that db.py reads DYNAMODB_ENDPOINT at module level (not lazily).
    If this changes the load_dotenv ordering requirement changes too — this
    test ensures we notice and update accordingly.
    """
    db_py = MAIN_PY.parent / "db.py"
    source = db_py.read_text()
    stmts = _statements(source)

    # Look for a module-level assignment that calls os.getenv("DYNAMODB_ENDPOINT")
    found = False
    for node in stmts:
        if not isinstance(node, ast.Assign):
            continue
        call = node.value
        if (
            isinstance(call, ast.Call)
            and isinstance(call.func, ast.Attribute)
            and call.func.attr == "getenv"
            and call.args
            and isinstance(call.args[0], ast.Constant)
            and call.args[0].value == "DYNAMODB_ENDPOINT"
        ):
            found = True
            break

    assert found, (
        "db.py no longer reads DYNAMODB_ENDPOINT at module level. "
        "Review whether the load_dotenv() ordering requirement in main.py "
        "is still necessary and update test_load_dotenv_called_before_local_app_imports."
    )
