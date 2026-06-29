# 📁 app/schemas/base.py

from pydantic import BaseModel
from typing import Optional, Generic, TypeVar, List

T = TypeVar("T")


# ── Base success response ──────────────────────────────────────────────────────
class BaseResponse(BaseModel):
    success: bool = True
    code:    int  = 200
    message: str  = "Success"


class DataResponse(BaseResponse, Generic[T]):
    data: T


class ListResponse(BaseResponse, Generic[T]):
    data: List[T]


# ── Helper: build response with dynamic code ───────────────────────────────────
def success_response(
    data=None,
    message: str = "Success",
    code: int = 200,
) -> dict:
    """
    Build a consistent success response dict with dynamic HTTP code.
    Use this in routes instead of schema classes.
    """
    response = {
        "success": True,
        "code":    code,
        "message": message,
    }
    if data is not None:
        response["data"] = data
    return response


def paginated_response(
    data: list,
    meta: dict,
    code: int = 200,
) -> dict:
    return {
        "success": True,
        "code":    code,
        "data":    data,
        "meta":    meta,
    }