To release a new version:
- Open a shell at the proper place (something as X:\robocorpws\vscode-extension\sema4ai)
- Checkout the `master` branch
- Update version using `python -m dev set-version 2.3.0`.
 -Update README.md to add notes on features/fixes.
- Update changelog.md to add notes on features/fixes and set release date.
- Commit your changes using the following message: ```Release Sema4.ai VSCode extension 2.3.0```
- Create a tag using `git tag sema4ai-2.3.0`.
- Push your changes using `git push`