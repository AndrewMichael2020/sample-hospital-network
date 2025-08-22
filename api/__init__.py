"""
Extended API package for healthcare scenarios.
"""

__version__ = "1.0.0"

# NOTE: Do not export the application at package level to avoid accidental
# use of `uvicorn api:app` which may import a stale/partial package state.
# Prefer explicit `uvicorn api.main:app` to run the application.

__all__ = ["__version__"]