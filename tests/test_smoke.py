import importlib
import pytest


def test_app_factory_imports():
    try:
        mod = importlib.import_module('app')
    except ModuleNotFoundError as exc:
        missing = exc.name or ""
        if missing.startswith('flask'):
            pytest.skip(f"Optional Flask extension '{missing}' not installed in CI environment")
        raise

    assert hasattr(mod, 'create_app') or hasattr(mod, 'app')


def test_requirements_loaded():
    # Basic runtime libraries should import without error
    for pkg in ['flask', 'requests']:
        importlib.import_module(pkg)
