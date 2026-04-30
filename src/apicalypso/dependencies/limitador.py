"""
dependencies/limitador.py

Este módulo configura un limitador de peticiones para la API utilizando SlowAPI.
"""

from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)