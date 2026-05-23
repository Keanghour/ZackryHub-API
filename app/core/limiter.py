# 📁 app/core/limiter.py

from slowapi import Limiter
from slowapi.util import get_remote_address

# Use client IP as the key for rate limiting
limiter = Limiter(key_func=get_remote_address)