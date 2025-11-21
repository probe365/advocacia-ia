import importlib


def test_app_factory_imports():
    mod = importlib.import_module('app')
    assert hasattr(mod, 'create_app') or hasattr(mod, 'app')


def test_requirements_loaded():
    # Basic runtime libraries should import without error
    for pkg in ['flask', 'requests']:
        importlib.import_module(pkg)
