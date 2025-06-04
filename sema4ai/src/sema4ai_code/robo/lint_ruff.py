import json
import sys
from typing import Any, Dict, List

from sema4ai_ls_core.core_log import get_logger
from sema4ai_ls_core.options import DEFAULT_TIMEOUT, USE_TIMEOUTS
from sema4ai_ls_core.protocols import IDocument

log = get_logger(__name__)

# F501–F509, F521–F525: Formatting errors Can raise exceptions at runtime (e.g., TypeError, KeyError).
# F621–F622: Star unpacking errors Syntax errors, prevents code from running.
# F633–F634: Logic/syntax errors Can result in unreachable or always-true branches; may hide bugs.
# F701–F707: Misplaced control flow Critical — break, return, etc. outside their legal scope.
# F722: forward-annotation-syntax-error Prevents parsing of function annotations.
# F821: undefined-name Runtime NameError. Critical.
# F823: undefined-local Runtime UnboundLocalError. Critical

SELECTED_RUFF_ERRORS = (
    "F501,F502,F503,F504,F505,F506,F507,F508,F509,"
    "F521,F522,F523,F524,F525,"
    "F621,F622,"
    "F633,F634,"
    "F701,F702,F704,F706,F707,"
    "F722,"
    "F821,F823"
)


def collect_ruff_errors(doc: IDocument) -> List[Dict[str, Any]]:
    """
    Run ruff linter on the given source code and return the results in a format
    compatible with LSP diagnostics.
    """

    try:
        import subprocess
        from pathlib import Path

        from sema4ai_ls_core import uris

        # Get the filename from the URI
        fs_path = uris.to_fs_path(doc.uri)
        filename = Path(fs_path).name

        # Run ruff check with JSON output using stdin
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "ruff",
                "check",
                "--select",
                SELECTED_RUFF_ERRORS,
                "--output-format=json",
                f"--stdin-filename={filename}",
            ],
            input=doc.source,
            capture_output=True,
            text=True,
            timeout=DEFAULT_TIMEOUT if USE_TIMEOUTS else None,
        )

        if result.returncode == 0:
            return []

        # Parse the JSON output
        diagnostics = []
        for diagnostic in json.loads(result.stdout):
            code = diagnostic.get("code")
            severity = (
                1 if code is None else _get_severity(code)
            )  # No code means SyntaxError

            lsp_diagnostic = {
                "range": {
                    "start": {
                        "line": diagnostic["location"]["row"] - 1,  # Convert to 0-based
                        "character": diagnostic["location"]["column"] - 1,
                    },
                    "end": {
                        "line": diagnostic["end_location"]["row"] - 1,
                        "character": diagnostic["end_location"]["column"] - 1,
                    },
                },
                "severity": severity,
                "source": "sema4ai-lint",
                "message": diagnostic["message"],
                "code": code or "SyntaxError",
            }
            diagnostics.append(lsp_diagnostic)

        return diagnostics

    except Exception as e:
        log.error(f"Error running ruff: {str(e)}")
        return []


def check_folder_for_ruff_errors(folder_path: str) -> list[dict] | None:
    """
    Check all Python files in the given folder for ruff errors.
    Returns a tuple of (file_path, line_number, error_message) for the first error found,
    or None if no errors are found.
    """
    try:
        import subprocess

        # Run ruff check on the folder (it will automatically handle all Python files inside)
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "ruff",
                "check",
                "--select",
                SELECTED_RUFF_ERRORS,
                "--output-format=json",
                folder_path,
            ],
            capture_output=True,
            text=True,
            timeout=(DEFAULT_TIMEOUT * 2) if USE_TIMEOUTS else None,
        )

        if result.returncode == 0:
            return None

        # Parse the JSON output and return the first error
        diagnostics = json.loads(result.stdout)
        if not diagnostics:
            return None

        return diagnostics
    except Exception as e:
        log.error(f"Error running ruff on folder: {str(e)}")
        return None


def _get_severity(code: str) -> int:
    if code.startswith("E"):  # Error
        return 1
    elif code.startswith("F"):  # Fatal
        return 1
    elif code.startswith("W"):  # Warning
        return 2
    else:  # Default to warning
        return 2
