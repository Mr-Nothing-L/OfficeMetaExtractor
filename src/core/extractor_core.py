"""Public entry point for MetaExtractor.

When the Cython extension is present, it shadows this module and provides
a compiled wrapper around the Python implementation in _extractor_core.py.
"""
from ._extractor_core import MetaExtractor

__all__ = ["MetaExtractor"]
