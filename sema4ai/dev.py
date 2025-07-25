"""
This is a script to help with the automation of common development tasks.

It requires 'fire' to be installed for the command line automation (i.e.: pip install fire).

Some example commands:

    python -m dev set-version 0.0.2
    python -m dev check-tag-version
    python -m dev vendor-robocorp-ls-core
"""

import os
import subprocess
import sys
import traceback
from pathlib import Path

__file__ = os.path.abspath(__file__)

if not os.path.exists(os.path.join(os.path.abspath("."), "dev.py")):
    raise RuntimeError('Please execute commands from the directory containing "dev.py"')

try:
    import sema4ai_code
except ImportError:
    # I.e.: add relative path (the cwd must be the directory containing this file).
    sys.path.append("src")
    import sema4ai_code

sema4ai_code.import_robocorp_ls_core()

root = Path(__file__).parent.parent


def _fix_contents_version(contents, version):
    import re

    contents = re.sub(r"(version\s*=\s*)\"\d+\.\d+\.\d+", rf'\1"{version}', contents)
    contents = re.sub(
        r"(__version__\s*=\s*)\"\d+\.\d+\.\d+", rf'\1"{version}', contents
    )
    contents = re.sub(
        r"(\"version\"\s*:\s*)\"\d+\.\d+\.\d+", rf'\1"{version}', contents
    )

    return contents


def _fix_rcc_contents_version(contents, version):
    import re

    assert version.startswith("v"), f'{version} must start with "v"'

    # RCC_VERSION = "v11.5.5"
    # const RCC_VERSION = "v11.5.5";
    contents = re.sub(
        r"(RCC_VERSION\s*=\s*)\"v\d+\.\d+\.\d+", rf'\1"{version}', contents
    )

    # RCC_VERSION: v11.5.5 (YAML style)
    contents = re.sub(r"(RCC_VERSION\s*:\s*)v\d+\.\d+\.\d+", rf"\1{version}", contents)

    # Change `rcc/releases/v18.3.0/` to `rcc/releases/v18.5.0/`
    contents = re.sub(
        r"rcc/releases/v\d+\.\d+\.\d+/", rf"rcc/releases/{version}/", contents
    )

    return contents


class Dev:
    # CI call: python -m dev set-version
    def set_version(self, version):
        """
        Sets a new version for sema4ai in all the needed files.
        """

        def update_version(version, filepath):
            with open(filepath) as stream:
                contents = stream.read()

            new_contents = _fix_contents_version(contents, version)
            assert contents != new_contents
            with open(filepath, "w") as stream:
                stream.write(new_contents)

        update_version(version, os.path.join(".", "package.json"))
        update_version(version, os.path.join(".", "pyproject.toml"))
        update_version(version, os.path.join(".", "src", "sema4ai_code", "__init__.py"))

    def set_rcc_version(self, version):
        """
        Sets the new RCC version to be used.
        """

        def update_version(version, filepath):
            with open(filepath) as stream:
                contents = stream.read()

            new_contents = _fix_rcc_contents_version(contents, version)
            assert contents != new_contents, (
                f"Nothing changed after applying new version (file: {filepath})"
            )
            with open(filepath, "w") as stream:
                stream.write(new_contents)

        update_version(version, os.path.join(".", "bin", "develop.sh"))
        update_version(version, os.path.join(".", "bin", "develop.bat"))
        update_version(version, os.path.join(".", "src", "sema4ai_code", "rcc.py"))
        update_version(version, os.path.join(".", "vscode-client", "src", "rcc.ts"))
        update_version(
            version,
            os.path.join(root, ".github", "workflows", "build_environments.yaml"),
        )

        print(
            f"New RCC version set.\nErase the rcc executable from {os.path.abspath(os.path.join('.', 'bin'))} to re-download locally."
        )

    def get_tag(self):
        import subprocess

        # i.e.: Gets the last tagged version
        cmd = "git describe --tags --abbrev=0 --match sema4ai*".split()
        popen = subprocess.Popen(cmd, stdout=subprocess.PIPE)
        stdout, stderr = popen.communicate()

        # Something as: b'sema4ai-0.0.1'
        stdout = stdout.decode("utf-8")
        stdout = stdout.strip()
        return stdout

    def check_tag_version(self):
        """
        Checks if the current tag matches the latest version (exits with 1 if it
        does not match and with 0 if it does match).
        """
        import subprocess

        version = self.get_tag()
        version = version[version.rfind("-") + 1 :]

        if sema4ai_code.__version__ == version:
            sys.stderr.write(f"Version matches ({version}) (exit(0))\n")
            sys.exit(0)
        else:
            sys.stderr.write(
                "Version does not match (found in sources: %s != tag: %s) (exit(1))\n"
                % (sema4ai_code.__version__, version)
            )
            sys.exit(1)

    def remove_vendor_robocorp_ls_core(self):
        import shutil
        import time

        vendored_dir = os.path.join(
            os.path.dirname(__file__),
            "src",
            "sema4ai_code",
            "vendored",
            "sema4ai_ls_core",
        )
        try:
            shutil.rmtree(vendored_dir)
            time.sleep(0.5)
        except:
            if os.path.exists(vendored_dir):
                traceback.print_exc()
        return vendored_dir

    def vendor_robocorp_ls_core(self):
        """
        Vendors sema4ai_ls_core into sema4ai_code/vendored.
        """
        import shutil

        src_core = os.path.join(
            os.path.dirname(__file__),
            "..",
            "sema4ai-python-ls-core",
            "src",
            "sema4ai_ls_core",
        )
        vendored_dir = self.remove_vendor_robocorp_ls_core()
        print(f"Copying from: {src_core} to {vendored_dir}")

        shutil.copytree(src_core, vendored_dir)
        print("Finished vendoring.")

    def codegen(self):
        """
        Generates code (to add actions, settings, etc).
        In particular, generates the package.json and auxiliary files with
        constants in the code.
        """

        try:
            import codegen_package
        except ImportError:
            # I.e.: add relative path (the cwd must be the directory containing this file).
            sys.path.append("codegen")
            import codegen_package
        codegen_package.main()

    # CI call: python -m dev fix-readme
    def fix_readme(self):
        """
        Updates the links in the README.md to match the current tagged version.
        To be called during release.
        """
        import re

        readme = os.path.join(os.path.dirname(__file__), "README.md")
        with open(readme) as f:
            content = f.read()

        tag = self.get_tag()
        if not tag:
            raise AssertionError(
                "Could not get tag! (are you checking out with full tag history?)"
            )

        new_content = re.sub(
            r"\(docs/",
            rf"(https://github.com/Sema4AI/vscode-extension/tree/{tag}/docs/",
            content,
        )

        new_content = re.sub(
            r"\(images/",
            rf"(https://raw.githubusercontent.com/Sema4AI/vscode-extension/{tag}/sema4ai/images/",
            content,
        )

        new_content = new_content.replace(
            "Apache 2.0",
            "[Sema4.ai License Agreement (pdf)](https://sema4.ai/cdn/downloads/legal/Sema4ai-EULA-v1.0.pdf)",
        )

        assert "apache" not in new_content.lower()
        with open(readme, "w") as f:
            f.write(new_content)

    def generate_license_file(self):
        import os
        import urllib.request

        url = "https://sema4.ai/cdn/downloads/legal/Sema4ai-EULA-v1.0.txt"
        readme = os.path.join(os.path.dirname(__file__), "LICENSE.txt")

        request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(request) as response:
            content = response.read().decode("utf-8")

        with open(readme, "w") as f:
            f.write(content)

        # Read the content back from LICENSE.txt for verification
        with open(readme) as f:
            written_content = f.read()
        assert "Sema4.ai End User License Agreement" in written_content

    def download_rcc(self, plat):
        assert plat in ("win32", "linux", "darwin", "darwin-arm64")
        import stat
        import time

        from sema4ai_code.rcc import download_rcc

        root = os.path.dirname(__file__)
        bin_dir = os.path.join(root, "bin")
        assert os.path.exists(bin_dir)

        rcc_location_win = os.path.join(bin_dir, "rcc.exe")
        if os.path.exists(rcc_location_win):
            os.chmod(rcc_location_win, stat.S_IWRITE)
            os.remove(rcc_location_win)
            time.sleep(0.1)

        rcc_location_linux_darwin = os.path.join(bin_dir, "rcc")
        if os.path.exists(rcc_location_linux_darwin):
            os.chmod(rcc_location_linux_darwin, stat.S_IWRITE)
            os.remove(rcc_location_linux_darwin)
            time.sleep(0.1)

        assert not os.path.exists(rcc_location_win)
        assert not os.path.exists(rcc_location_linux_darwin)

        if plat == "win32":
            rcc_location = rcc_location_win
        else:
            rcc_location = rcc_location_linux_darwin

        download_rcc(rcc_location, force=True, sys_platform=plat)
        time.sleep(0.2)
        print(f"Downloaded rcc to: {rcc_location}")
        assert os.path.exists(rcc_location)

    def local_install(self):
        """
        Packages both Robotframework Language Server and Sema4.ai and installs
        them in Visual Studio Code.
        """
        print("Making local install")

        def run(args, shell=False):
            print("---", " ".join(args))
            return subprocess.check_call(args, cwd=curdir, shell=shell)

        def get_version():
            import json

            p = Path(curdir / "package.json")
            contents = json.loads(p.read_text())
            return contents["version"]

        print("\n--- installing Sema4.ai")
        curdir = root / "sema4ai"
        run("python -m dev vendor_robocorp_ls_core".split())
        run("vsce package".split(), shell=sys.platform == "win32")
        run(
            f"code --install-extension sema4ai-{get_version()}.vsix".split(),
            shell=sys.platform == "win32",
        )
        run("python -m dev remove_vendor_robocorp_ls_core".split())

    def ruff_format(self, format=False):
        """
        To format:
        python -m dev ruff_format --format

        To check:
        python -m dev ruff_format
        """

        def run(args):
            print("---", " ".join(args))
            return subprocess.check_call(args, cwd=root)

        check_str = ""
        if not format:
            check_str = "--check"

        run(
            f"ruff format {check_str} . --exclude=vendored --exclude=libs".split(),
        )


def test_lines():
    """
    Check that the replace matches what we expect.

    Things we must match:

        version="0.0.1"
        "version": "0.0.1",
        __version__ = "0.0.1"
    """
    from sema4ai_ls_core.unittest_tools.compare import compare_lines

    contents = _fix_contents_version(
        """
        version="0.0.198"
        version = "0.0.1"
        "version": "0.0.1",
        "version":"0.0.1",
        "version" :"0.0.1",
        __version__ = "0.0.1"
        """,
        "3.7.1",
    )

    expected = """
        version="3.7.1"
        version = "3.7.1"
        "version": "3.7.1",
        "version":"3.7.1",
        "version" :"3.7.1",
        __version__ = "3.7.1"
        """

    compare_lines(contents.splitlines(), expected.splitlines())


if __name__ == "__main__":
    TEST = False
    if TEST:
        test_lines()
    else:
        try:
            import fire
        except ImportError:
            sys.stderr.write(
                '\nError. "fire" library not found.\nPlease install with "pip install fire" (or activate the proper env).\n'
            )
        else:
            # Workaround so that fire always prints the output.
            # See: https://github.com/google/python-fire/issues/188
            def Display(lines, out):
                text = "\n".join(lines) + "\n"
                out.write(text)

            from fire import core

            core.Display = Display

            fire.Fire(Dev())
