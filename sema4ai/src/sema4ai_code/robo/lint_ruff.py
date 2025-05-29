import json
from typing import List, Dict, Any, Optional, Tuple
from sema4ai_ls_core.core_log import get_logger
from sema4ai_ls_core.protocols import IDocument

log = get_logger(__name__)


def collect_ruff_errors(doc: IDocument) -> List[Dict[str, Any]]:
    """
    Run ruff linter on the given source code and return the results in a format
    compatible with LSP diagnostics.
    """
    from sema4ai_ls_core.options import DEFAULT_TIMEOUT

    try:
        import subprocess
        from sema4ai_ls_core import uris
        from pathlib import Path

        # Get the filename from the URI
        fs_path = uris.to_fs_path(doc.uri)
        filename = Path(fs_path).name

        # Run ruff check with JSON output using stdin
        result = subprocess.run(
            [
                "ruff",
                "check",
                "--select",
                "F,B",
                "--ignore",
                "F401,F403,F405,F841",
                "--output-format=json",
                f"--stdin-filename={filename}",
            ],
            input=doc.source,
            capture_output=True,
            text=True,
            timeout=DEFAULT_TIMEOUT
        )

        if result.returncode == 0:
            return []

        # Parse the JSON output
        diagnostics = []
        for diagnostic in json.loads(result.stdout):
            code = diagnostic.get("code")
            severity = 1 if code is None else _get_severity(code) # No code means SyntaxError

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
                "code": code or "SyntaxError"
            }
            diagnostics.append(lsp_diagnostic)

        return diagnostics

    except Exception as e:
        log.error(f"Error running ruff: {str(e)}")
        return []


def check_folder_for_ruff_errors(folder_path: str) -> Optional[Tuple[str, int, str]]:
    """
    Check all Python files in the given folder for ruff errors.
    Returns a tuple of (file_path, line_number, error_message) for the first error found,
    or None if no errors are found.
    """
    try:
        import subprocess
        from pathlib import Path

        # Run ruff check on the folder (it will automatically handle all Python files inside)
        result = subprocess.run(
            [
                "ruff",
                "check",
                "--select",
                "F,B",
                "--ignore",
                "F401,F403,F405,F841",
                "--output-format=json",
                folder_path
            ],
            capture_output=True,
            text=True,
            timeout=30  # Increased timeout for multiple files
        )

        if result.returncode == 0:
            return None

        # Parse the JSON output and return the first error
        diagnostics = json.loads(result.stdout)
        if not diagnostics:
            return None

        first_error = diagnostics[0]
        file_path = first_error["filename"]
        line_number = first_error["location"]["row"]
        error_message = first_error["message"]

        return (file_path, line_number, error_message)

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
