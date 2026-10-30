from sqlalchemy import ColumnElement, and_, true
from sqlalchemy.orm import InstrumentedAttribute

from app.core.text import fold


def escape_like(term: str) -> str:
    """Makes %, _ and \\ in user input match literally; pair with `escape="\\\\"` in LIKE."""
    return term.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def contains_words(column: InstrumentedAttribute[str], term: str) -> ColumnElement[bool]:
    """Every word of `term`, in any order, somewhere in a column that holds `fold()`ed text."""
    return and_(
        true(), *(column.like(f"%{escape_like(word)}%", escape="\\") for word in fold(term).split())
    )
