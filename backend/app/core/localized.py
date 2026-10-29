from typing import Annotated, Any, overload

from pydantic import BaseModel, StringConstraints


class LocalizedText(BaseModel):
    """Catalog text in both UI languages; the SPA picks one, so switching is instant."""

    vi: str
    en: str


ShortText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=255)]
LongText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=500)]


class LocalizedName(BaseModel):
    vi: ShortText
    en: ShortText


class LocalizedDescription(BaseModel):
    vi: LongText
    en: LongText


class LocalizedColumns:
    """Exposes a `<field>_vi` / `<field>_en` column pair as one `{"vi", "en"}` value.

    Reading gives a dict that `LocalizedText` validates; assigning a dict or a localized
    input model writes both columns.
    """

    def __init__(self, field: str):
        self.field = field

    @overload
    def __get__(self, obj: None, owner: type) -> "LocalizedColumns": ...
    @overload
    def __get__(self, obj: object, owner: type) -> dict[str, str]: ...
    def __get__(self, obj: object | None, owner: type) -> Any:
        if obj is None:
            return self
        return {"vi": getattr(obj, f"{self.field}_vi"), "en": getattr(obj, f"{self.field}_en")}

    def __set__(self, obj: object, value: dict[str, str] | BaseModel) -> None:
        values = value.model_dump() if isinstance(value, BaseModel) else value
        setattr(obj, f"{self.field}_vi", values["vi"])
        setattr(obj, f"{self.field}_en", values["en"])
