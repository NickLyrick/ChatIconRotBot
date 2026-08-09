"""Shared pytest configuration.

``src.bot.settings`` reads its configuration from the environment at import
time and aiogram validates the token eagerly, so placeholders have to be in
place before anything under ``src`` is imported. Being at the repository root,
this module is loaded before any test module, which is early enough.

The root itself reaches ``sys.path`` through ``pythonpath`` in pytest.ini.
"""

import os

# A syntactically valid but fake token — aiogram rejects malformed ones.
os.environ.setdefault("TOKEN", "123456789:AAHdqTcvCH1vGWJxfSeofSAs0K5PALDsaw")
os.environ.setdefault(
    "DATABASE_URL", "postgresql+asyncpg://user:password@localhost:5432/test"
)
