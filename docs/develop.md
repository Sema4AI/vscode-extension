## Developing

🚀 Base installations and first run

### Prerequisites

- **Node.js**: Node 24.21.0 (pinned in [`sema4ai/.nvmrc`](/sema4ai/.nvmrc), which all GitHub workflows also use).
  Install [NVM](https://github.com/nvm-sh/nvm?tab=readme-ov-file#installing-and-updating) to manage Node versions
  - `nvm install 24.21.0` - installs correct Node version
  - `nvm use 24.21.0` - switch to the correct version
  - Verify installation:
    - `node --version`
    - `npm --version`

- **Python**: Python 3.11 (see [pyproject.toml](/sema4ai/pyproject.toml) for exact version requirements)
- **Poetry** 2.x: manages the Python development environment (`pip install poetry` or `pipx install poetry`)
- **vsce**: For packaging VSIX files [@vscode/vsce](https://www.npmjs.com/package/@vscode/vsce) - installed as a dev dependency via npm 

### Initial Setup

1. Go to `/sema4ai` folder and install Node dependencies:
   ```bash
   npm install
   ```

2. Set up the Poetry environment (see "Python development environment (Poetry)" below)

3. Open `/sema4ai/.vscode/sema4ai-code.code-workspace` in VS Code and run debug
   - ![](/docs/vscode-workspace.png)
   - A new VS Code window should pop-up with the VS Code extension in play.

## Python development environment (Poetry)

🏗️ The extension backend, the `dev.py` helper commands and the Python tests all run in a
[Poetry](https://python-poetry.org/) virtual environment defined by [`sema4ai/pyproject.toml`](/sema4ai/pyproject.toml).
It includes the development tools (`fire` for `dev.py`, `pytest`, `mypy`, `ruff`) and installs
`sema4ai-python-ls-core` from `../sema4ai-python-ls-core` in editable mode.

### Setup Steps

Run these in the `/sema4ai` directory:

1. If your default `python` is not 3.11, tell Poetry which interpreter to use:
   ```bash
   poetry env use 3.11        # or a full path, e.g. poetry env use C:\Python311\python.exe
   ```
2. Optional: keep the environment in `/sema4ai/.venv` (git-ignored) instead of Poetry's cache directory.
   This writes a `poetry.toml` in `/sema4ai`; it's a personal setting, so don't commit it:
   ```bash
   poetry config virtualenvs.in-project true --local
   ```
3. Install the dependencies:
   ```bash
   poetry install
   ```
   Run `poetry install` again whenever `pyproject.toml` or `poetry.lock` changes.
   Add `--sync` to also remove packages that are no longer in the lock file.
4. Find the environment's location (needed for the IDE interpreter):
   ```bash
   poetry env info --path
   ```
   By default this is under Poetry's cache, e.g.
   `%LOCALAPPDATA%\pypoetry\Cache\virtualenvs\sema4ai-vscode-extension-<hash>-py3.11` on Windows
   or `.venv` if you did step 2.
5. In VS Code, run `Python: Select Interpreter` and pick `<env path>/Scripts/python.exe` (Windows)
   or `<env path>/bin/python` (Linux/macOS).

### Running commands in the Poetry environment

There are two ways to run anything Python-based from this guide, always from the `/sema4ai` directory
(or below it, e.g. `/sema4ai/tests`):

- **Prefix each command with `poetry run`** (no activation needed). This is what the rest of this guide uses:
  ```bash
  poetry run python -m dev codegen
  ```
- **Activate the environment once per shell** and then run commands without the prefix.
  Poetry 2.x no longer has `poetry shell`; use `poetry env activate`, which prints the activation command:
  ```powershell
  # PowerShell
  Invoke-Expression (poetry env activate)
  ```
  ```bash
  # bash / zsh
  eval $(poetry env activate)
  ```
  After this, `python -m dev codegen` uses the Poetry environment. Run `deactivate` to leave it.

> Running `python -m dev ...` with a Python that is not the Poetry environment fails with
> `"fire" library not found` (or, for `codegen`, `No module named 'sema4ai_code'`).

### Available Python Dev Commands

Run `poetry run python -m dev` to list all available commands. Common ones include:

- `poetry run python -m dev codegen` - Generate code (package.json, constants, etc.)
- `poetry run python -m dev local_install` - Build and install VSIX locally
- `poetry run python -m dev vendor-robocorp-ls-core` - Vendor the language server core
- `poetry run python -m dev remove-vendor-robocorp-ls-core` - Remove vendored core
- `poetry run python -m dev set-version <version>` - Set version in all files
- `poetry run python -m dev set-rcc-version <version>` - Set RCC version
- `poetry run python -m dev ruff_format` - Check Python formatting
- `poetry run python -m dev ruff_format --format` - Format Python code

### `sema4ai-python-ls-core`

[`/sema4ai-python-ls-core`](/sema4ai-python-ls-core) is a separate Poetry project with its own `pyproject.toml` and
`poetry.lock`. The `/sema4ai` environment already includes it, so you only need a separate environment there
when working on it on its own (e.g. running its tests or mypy): run `poetry install` and `poetry run ...`
inside `/sema4ai-python-ls-core`.

## Building and Compiling

### TypeScript/Node.js

From the `/sema4ai` directory:

- **Compile TypeScript**: `npm run compile`
- **Watch mode** (auto-compile on changes): `npm run watch`
- **Format check**: `npm run prettier`
- **Format fix**: `npm run prettier-fix`

### Python

From the `/sema4ai` directory:

- **Format Python code**: `poetry run python -m dev ruff_format --format`
- **Check Python formatting**: `poetry run python -m dev ruff_format`
- **Type check**: `poetry run mypy --follow-imports=silent --show-column-numbers src tests codegen`
- **Generate code** (after adding commands/settings): `poetry run python -m dev codegen`
- **Vendor language server core**: `poetry run python -m dev vendor-robocorp-ls-core`

## Building a VSIX locally

From the `/sema4ai` directory:

```bash
poetry run python -m dev local_install
```

This will:
1. Vendor the language server core
2. Package the extension as a VSIX
3. Install it in VS Code
4. Remove the vendored core

Alternatively, to just package without installing:
```bash
poetry run python -m dev vendor-robocorp-ls-core
npm run vsce:package
poetry run python -m dev remove-vendor-robocorp-ls-core
```

## Testing

### TypeScript Tests

From the `/sema4ai` directory:

```bash
npm test
```

This will compile the TypeScript code and run the test suite located in `vscode-client/src/tests/`.

### Python Tests

From the `/sema4ai/tests` directory:

```bash
poetry run python -u ../../sema4ai-python-ls-core/tests/run_tests.py -rfE -otests_output -vv -n 1 -m "not data_server and not rcc_env" .
```

To run a single test file or test:

```bash
poetry run python -m pytest sema4ai_code_tests/test_rcc.py
poetry run python -m pytest "sema4ai_code_tests/test_rcc.py::test_rcc_template_names"
```

For integration tests, see `/sema4ai/tests/sema4ai_code_tests/test_vscode_integration.py`.

Notes:
- Tests require the Poetry environment (see "Python development environment (Poetry)" above).
- Many tests use the `ci_endpoint` fixture, which requires the `CI_ENDPOINT` environment variable
  (CI uses a repository secret). For tests that don't actually call the cloud, any value works
  (e.g. `CI_ENDPOINT=https://ci.invalid`).

## Adding a new command

To add a new command, add it at the `COMMANDS` in `/sema4ai/codegen/commands.py` and then execute
(in a shell in the `/sema4ai` directory) `poetry run python -m dev codegen`.

This should add the command to the `package.json` as well as the files related to the constants.

Then, you may handle the command either in `/sema4ai/vscode-client/src/extension.ts` if the
command requires some VSCode-only API or in the language server (which is ideal as less work would
be required when porting the extension to a different client).

Note: that it's also possible to have one command call another command, so, if needed the command could start
on the client and then call parts of it on the server.

Note: the code in the extension side (in TypeScript) should be kept to a minimum (as it needs to be
redone if porting to a different client).

Note: at least one integration test for each action must be added in
`/sema4ai/tests/sema4ai_code_tests/test_vscode_integration.py`

## Adding a new setting

To add a new setting, add it at the `SETTINGS` in `/sema4ai/codegen/settings.py` and then execute
(in a shell in the `/sema4ai` directory) `poetry run python -m dev codegen`.

## Updating the extension Python environment

We prebuilt the Python env. that the extension it self needs using RCC.

1. The dependencies are set based in [`/sema4ai/bin/create_env/`](/sema4ai/bin/create_env/) `conda.yaml` files.
   - Update all of these in sync  
3. Once updated the environment builds are handled by GHA
   - https://github.com/Sema4AI/vscode-extension/actions/workflows/build_environments.yaml
4. After the runs are done, the file: `/sema4ai/vscode-client/src/rcc.ts` needs to be updated to set the `BASENAME_PREBUILT_XXX` global variables based on the new paths.
5. Also, the `pyproject.toml` should be updated so that the python development environment is updated accordingly.

## Updating RCC

- Check RCC versions from [changelog](https://github.com/Sema4AI/rcc/blob/master/docs/changelog.md)
- In a shell in the `/sema4ai` directory run: `poetry run python -m dev set-rcc-version 20.3.3`
- Remove the rcc executable from the `bin` folder to redownload the next time the extension is executed.
