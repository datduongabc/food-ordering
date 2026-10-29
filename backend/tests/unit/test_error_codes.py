"""The SPA translates errors by `code`, so every domain error raised in app/ must carry one.

A missing code would only fail at runtime (TypeError -> 500) on whichever path raised it,
so this checks the source statically instead of relying on each path being exercised.
"""

import ast
import re
from pathlib import Path

import app
from app.core import errors

APP_DIR = Path(app.__file__).parent
DOMAIN_ERRORS = {
    name
    for name, obj in vars(errors).items()
    if isinstance(obj, type) and issubclass(obj, errors.AppError)
}


def domain_raises() -> list[tuple[str, ast.Call]]:
    found = []
    for path in sorted(APP_DIR.rglob("*.py")):
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if (
                isinstance(node, ast.Raise)
                and isinstance(node.exc, ast.Call)
                and isinstance(node.exc.func, ast.Name)
                and node.exc.func.id in DOMAIN_ERRORS
            ):
                found.append((f"{path.relative_to(APP_DIR)}:{node.lineno}", node.exc))
    return found


def test_scan_finds_the_domain_errors():
    assert len(domain_raises()) > 40


def test_every_domain_error_has_a_snake_case_literal_code():
    for where, call in domain_raises():
        code = next((kw.value for kw in call.keywords if kw.arg == "code"), None)
        assert isinstance(code, ast.Constant), f"{where} raises without a literal code="
        assert re.fullmatch(r"[a-z]+(_[a-z]+)*", code.value), f"{where}: {code.value!r}"
