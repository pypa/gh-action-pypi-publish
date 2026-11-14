# Naming the Ducks

Canonical names for this project, and how to refer to it in
prose. Other files in `.agents-ctx/` (and any generated content)
should say "the project" rather than hardcoding one of these --
reach for a specific name only when the distinction actually
matters (e.g. citing a package, an import, or a repository URL).

## Action reference: `pypa/gh-action-pypi-publish`

This is a GitHub Action, not a Python distribution -- nothing is
published to PyPI. Workflows refer to it as
`pypa/gh-action-pypi-publish@<ref>`, usually `release/v1` or an
exact tag or commit SHA. In prose, "the PyPI publish action" or
`pypa/gh-action-pypi-publish`.

## GitHub repository slug: `pypa/gh-action-pypi-publish`

The same as the action reference. Use it verbatim when it's
actually the repository being referenced (URLs, `gh` invocations,
PR/issue citations).

## Branches

`unstable/v1` is the development branch PRs target; `release/v1`
is what users pin to, moved forward on releases. The `master`
branch is sunset. Say which one is meant.
