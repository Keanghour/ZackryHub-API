# 📁 app/core/exceptions.py

from fastapi import HTTPException, status


# ── Base app exception ─────────────────────────────────────────────────────────
class AppException(HTTPException):
    def __init__(self, status_code: int, message: str, error_code: str):
        super().__init__(
            status_code=status_code,
            detail={
                "success":        False,
                "code":           status_code,
                "message":        message,
                "error_messages": error_code,
            }
        )


# ── Inventory ──────────────────────────────────────────────────────────────────
class InsufficientStockException(AppException):
    def __init__(self, available_stock: int, requested_quantity: int):
        from app.core import error_codes
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            message="Insufficient stock",
            error_code=error_codes.INVENTORY_INSUFFICIENT_STOCK,
        )
        self.detail = {
            "success":        False,
            "code":           400,
            "message":        "Insufficient stock",
            "error_messages": error_codes.INVENTORY_INSUFFICIENT_STOCK,
            "error": {
                "available_stock":    available_stock,
                "requested_quantity": requested_quantity,
            },
        }