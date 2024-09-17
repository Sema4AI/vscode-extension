import os.path
import sys
from typing import Any


def _import_yaml():
    try:
        import yaml
    except ImportError:
        _parent_dir = os.path.dirname(__file__)
        _yaml_dir = os.path.join(_parent_dir, "libs", "yaml_lib")
        if not os.path.exists(_yaml_dir):
            raise RuntimeError(f"Expected: {_yaml_dir} to exist.")
        sys.path.append(_yaml_dir)
        import yaml  # @UnusedImport


def load(stream) -> Any:
    _import_yaml()
    import yaml

    return yaml.safe_load(stream)


def dumps(contents: Any) -> str:
    _import_yaml()
    import yaml

    return yaml.safe_dump(contents)
