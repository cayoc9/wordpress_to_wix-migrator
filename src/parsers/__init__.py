"""
Parsers and converters used by the migration pipeline.

This subpackage currently exposes :func:`convert_html_to_ricos` from
``src.parsers.ricos_parser``.
"""

from .ricos_parser import convert_html_to_ricos

__all__ = ["convert_html_to_ricos"]
