def escape_like(term: str) -> str:
    """Makes %, _ and \\ in user input match literally; pair with `escape="\\\\"` in LIKE."""
    return term.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
