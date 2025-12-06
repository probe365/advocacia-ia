"""Pytest configuration helpers for integration-heavy scripts."""
from __future__ import annotations

import os
import sys
from pathlib import Path

# Ensure repository root is on sys.path so direct script imports keep working
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Provide safe defaults for CI runs lacking secrets. Real runs should override
# these via the environment.
os.environ.setdefault("DATAJUD_API_KEY", "test-datajud-key")
os.environ.setdefault("OPENAI_API_KEY", "test-openai-key")
# Allow developers to opt-in to full integration tests locally.
os.environ.setdefault("RUN_PIPELINE_TESTS", os.getenv("RUN_PIPELINE_TESTS", "0"))
