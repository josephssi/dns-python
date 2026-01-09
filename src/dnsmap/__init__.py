__version__ = "0.1.0"

from .resolver import resolve_records
from .txtparser import parse_txt

__all__ = ["resolve_records", "parse_txt"]
