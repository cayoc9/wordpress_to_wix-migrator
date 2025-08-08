"""
Top-level package for the WordPress → Wix migration utility.

This package bundles all components required to extract posts from
WordPress exports, convert HTML to the Wix Rich Content format, upload
media to the Wix Media Manager, create draft posts, publish them, and
generate redirect maps.  Modules are split into subpackages:

* :mod:`src.extractors` – helpers to parse CSV or XML exports
* :mod:`src.parsers` – HTML to Ricos converters
* :mod:`src.migrators` – Wix API interactions
* :mod:`src.utils` – error logging and redirect CSV generation

The intention of this separation is to make the tool composable and
testable.  Each layer has no direct knowledge of configuration or
execution strategy; orchestration is handled in the migration_tool.
"""
