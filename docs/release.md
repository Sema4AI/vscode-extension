To release a new version:

- Open a shell at the proper place (something as X:\robocorpws\vscode-extension\sema4ai)
- Checkout the `master` branch and create a new branch from it (`release/2.4.0`)
- Update version using `python -m dev set-version 2.4.0`
- Update README.md to add notes on features/fixes
- Update changelog.md to add notes on features/fixes and set release date
- Commit your changes using the following message: `Release Sema4.ai VSCode extension 2.4.0`
- Create PR
- After PR is merged to master, update local repo and create a tag using `git tag sema4ai-2.4.0`
