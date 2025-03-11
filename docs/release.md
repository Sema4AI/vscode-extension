## Pre-Release

To release a new **pre-release** version:

1. Run the [Pre-release - Sema4.ai Extension](https://github.com/Sema4AI/vscode-extension/actions/workflows/pre-release-robocorp-code.yml) workflow with the bugfix version bumped.
   **Note:** It is important not to bump the major nor minor version.
   **Note:** Make sure all changes in the pre-release are under the _Unreleased_ section of the `/docs/changelog.md`
2. No other actions required. The GitHub action will take all the necessary actions to create and publish the pre-release

## Release

Stable releases usually bump the minor version. The patch version number is usually reserved for pre-releases.

To release a **STABLE** new version:

- Open a shell at the proper place (something as `X:\sema4ai\vscode-extension\sema4ai`)
- Checkout the `master` branch and create a new branch from it (`release/2.11.0`)
- Update version using `python -m dev set-version 2.11.0`
- Update README.md to add notes on features/fixes
- Update `/docs/changelog.md`:
  - Add a new section for the new version (including the release date)
  - Move all items from the _Unreleased_ section to the new section
- Commit your changes using the following message: `Release Sema4.ai VSCode extension 2.11.0`
- Create PR
- After PR is merged to master, update local repo and create a tag using `git tag sema4ai-2.11.0`
- Push the tag to origin running `git push origin tag sema4ai-2.11.0`
