## Developing

🚀 Base installations and first run

### Prerequisites

- **Node.js**: Install [NVM](https://github.com/nvm-sh/nvm?tab=readme-ov-file#installing-and-updating) to manage Node versions
  - `nvm install 20.19.6` - installs correct Node version
  - `nvm use 20.19.6` - switch to the correct version
  - Verify installation:
    - `node --version`
    - `npm --version`

- **Python**: Python 3.11 (see [pyproject.toml](/sema4ai/pyproject.toml) for exact version requirements)
- **Poetry**: For Python dependency management (`pip install poetry`)
- **vsce**: For packaging VSIX files [@vscode/vsce](https://www.npmjs.com/package/@vscode/vsce) - installed as a dev dependency via npm 

### Initial Setup

1. Go to `/sema4ai` folder and install Node dependencies:
   ```bash
   npm install
   ```

2. Set up Python environment (see "Creating a local environment for python backend development" below)

3. Open `/sema4ai/.vscode/sema4ai-code.code-workspace` in VS Code and run debug
   - ![](/docs/vscode-workspace.png)
   - A new VS Code window should pop-up with the VS Code extension in play.

## Creating a local environment for python backend development

🏗️ If you need to develop the extension backend you need the setup below.

> **Recommendation:** Create a Python Virtual Environment with whatever tool you like.
> Once you've created the env, activate it & then continue with the development installation.
> For information regarding which Python Version you should use, please consult the [pyproject.toml](/sema4ai/pyproject.toml) file.

### Setup Steps

1. Navigate to `/sema4ai` directory
2. Install Python dependencies with Poetry:
   ```bash
   poetry install
   ```
3. Configure your IDE to use the Python interpreter:
   - **VS Code**: Use the `Python: Select Interpreter` command and select `.venv/Scripts/python` (Windows) or `.venv/bin/python` (Linux/Mac)
   - The virtual environment will be created in `.venv/` by Poetry

### Available Python Dev Commands

From the `/sema4ai` directory, run `python -m dev` to see all available commands. Common ones include:

- `python -m dev codegen` - Generate code (package.json, constants, etc.)
- `python -m dev local_install` - Build and install VSIX locally
- `python -m dev vendor-robocorp-ls-core` - Vendor the language server core
- `python -m dev remove-vendor-robocorp-ls-core` - Remove vendored core
- `python -m dev set-version <version>` - Set version in all files
- `python -m dev set-rcc-version <version>` - Set RCC version
- `python -m dev ruff_format` - Check Python formatting
- `python -m dev ruff_format --format` - Format Python code

## Building and Compiling

### TypeScript/Node.js

From the `/sema4ai` directory:

- **Compile TypeScript**: `npm run compile`
- **Watch mode** (auto-compile on changes): `npm run watch`
- **Format check**: `npm run prettier`
- **Format fix**: `npm run prettier-fix`

### Python

From the `/sema4ai` directory:

- **Format Python code**: `python -m dev ruff_format --format`
- **Check Python formatting**: `python -m dev ruff_format`
- **Generate code** (after adding commands/settings): `python -m dev codegen`
- **Vendor language server core**: `python -m dev vendor-robocorp-ls-core`

## Building a VSIX locally

From the `/sema4ai` directory:

```bash
python -m dev local_install
```

This will:
1. Vendor the language server core
2. Package the extension as a VSIX
3. Install it in VS Code
4. Remove the vendored core

Alternatively, to just package without installing:
```bash
python -m dev vendor-robocorp-ls-core
npm run vsce:package
python -m dev remove-vendor-robocorp-ls-core
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

For integration tests, see `/sema4ai/tests/sema4ai_code_tests/test_vscode_integration.py`.

Note: Tests require the Python environment to be set up with `poetry install` (see "Creating a local environment for python backend development" below).

## Adding a new command

To add a new command, add it at the `COMMANDS` in `/sema4ai/codegen/commands.py` and then execute
(in a shell in the `/sema4ai` directory) `python -m dev codegen`.

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
(in a shell in the `/sema4ai` directory) `python -m dev codegen`.

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
- In a shell in the `/sema4ai` directory run: `python -m dev set-rcc-version 20.3.3`
- Remove the rcc executable from the `bin` folder to redownload the next time the extension is executed.
