"""
Extended API package for healthcare scenarios.
"""

__version__ = "1.0.0"

# Expose the FastAPI application at package level so `uvicorn api:app`
# works when the package is used as the ASGI module.
try:
	from .main import app  # noqa: F401
except Exception:
	# Import errors may occur during packaging or static analysis; keep
	# them silent here so tooling can still import the package.
	app = None

__all__ = ["__version__", "app"]