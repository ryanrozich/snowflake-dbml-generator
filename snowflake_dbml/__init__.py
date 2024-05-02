# snowflake_dbml/__init__.py
from .generator import generate_dbml
from .config import load_config

__all__ = ['generate_dbml', 'load_config']
