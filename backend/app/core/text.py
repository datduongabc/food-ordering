import unicodedata


def fold(text: str) -> str:
    """Accent- and case-blind form for search, so "pho bo" finds "Phở bò".

    Combining marks are dropped after decomposition; đ is a letter of its own, not a d with
    a mark, so it is mapped by hand. Runs of whitespace become one space.
    """
    decomposed = unicodedata.normalize("NFD", text.replace("đ", "d").replace("Đ", "D"))
    bare = "".join(ch for ch in decomposed if not unicodedata.combining(ch))
    return " ".join(bare.casefold().split())
