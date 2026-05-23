# 📁 app/routes/__init__.py

from .auth import router as auth_router
from .users import router as users_router
from .roles import router as roles_router

routes_controllers = [
    auth_router,
    users_router,
    roles_router,
]