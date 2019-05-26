# PyPI publish GitHub Action
This action allows you to upload your [Python distribution package](
https://packaging.python.org/glossary/#term-distribution-package) to
PyPI.


## Usage
To use the action simply add the following lines in the end of your
`.github/main.workflow`.

```hcl
action "Upload Python dist to PyPI" {
  uses = "re-actors/pypi-action@master"
  env = {
    TWINE_USERNAME = "f'{your_project}-bot'"
  }
  secrets = ["TWINE_PASSWORD"]
}
```

N.B. Use a valid tag, or branch, or commit SHA instead
of `master` to pin the action to use a specific version of it.


### Environment Variables and Secrets
- **`TWINE_USERNAME`**: set this one to the username used to authenticate
against PyPI. _It is recommended to have a separate user account like
`f'{your_project}-bot'` having the lowest privileges possible on your
target dist page._
- **`TWINE_PASSWORD`**: it's a password for the account used in
`TWINE_USERNAME` env var. **ATTENTION! WARNING! When adding this value
to the Action node in your workflow, use SECRETS, not normal env vars.**


## License
The Dockerfile and associated scripts and documentation in this project
are released under the [BSD 3-clause license](LICENSE.md).
