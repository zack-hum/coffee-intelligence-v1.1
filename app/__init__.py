"""Load settings before any module reads os.environ (see app/settings.py)."""

from . import settings  # noqa: F401
