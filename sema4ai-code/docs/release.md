Steps to do a new release
--------------------------

To release a new version:

- Open a shell at the proper place (something as `X:\robocorpws\vscode-extension\sema4ai-code`)

- Create release branch (`git branch -D release-sema4ai-code & git checkout -b release-sema4ai-code`)

- Update version (`python -m dev set-version 1.22.1`).

- Update README.md to add notes on features/fixes.

- Update changelog.md to add notes on features/fixes and set release date.

- Push contents to release branch, get the build in https://github.com/Sema4AI/vscode-extension//actions and install locally to test.
  - `mu acp Release Sema4.ai Code 1.22.1`

- Rebase with master (`git checkout master & git rebase release-sema4ai-code`).

- Create a tag (`git tag sema4ai-code-1.22.1`) and push it.
