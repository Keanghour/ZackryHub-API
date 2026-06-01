# 📁 app/core/exceptions.py

from fastapi import HTTPException, status
from app.core import error_codes


class InsufficientStockException(HTTPException):
    def __init__(self, available_stock: int, requested_quantity: int):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "success":    False,
                "message":    "Insufficient stock",
                "error_code": error_codes.INVENTORY_INSUFFICIENT_STOCK,
                "error": {
                    "available_stock":    available_stock,
                    "requested_quantity": requested_quantity,
                },
            }
        )