# PyPI publish GitHub Action
This action allows you to upload your [Python distribution package](
https://packaging.python.org/glossary/#term-distribution-package) to
PyPI.


## Usage

To use the action add the following step to your workflow file (e.g.:
`.github/workflows/main.yml`)


```yml
- name: Publish a Python distribution to PyPI
  uses: pypa/gh-action-pypi-publish@master
  with:
    user: __token__
    password: ${{ secrets.pypi_password }}
```

A common use case is to upload packages only on a tagged commit, to do so add a
filter to the step:


```yml
  if: github.event_name == 'push' && startsWith(github.event.ref, 'refs/tags')
```

So the full step would look like:


```yml
- name: Publish package
  if: github.event_name == 'push' && startsWith(github.event.ref, 'refs/tags')
  uses: pypa/gh-action-pypi-publish@master
  with:
    user: __token__
    password: ${{ secrets.pypi_password }}
```

The example above uses the new [API token](https://pypi.org/help/#apitoken)
feature of PyPI, which is recommended to restrict the access the action has.

The secret used in `${{ secrets.pypi_password }}` needs to be created on the settings
page of your project on GitHub. See [Creating & using secrets].


## Non-goals

This GitHub Action [has nothing to do with _building package
distributions_]. Users are responsible for preparing dists for upload
by putting them into the `dist/` folder prior to running this Action.


## License

The Dockerfile and associated scripts and documentation in this project
are released under the [BSD 3-clause license](LICENSE.md).


[Creating & using secrets]: https://help.github.com/en/articles/virtual-environments-for-github-actions#creating-and-using-secrets-encrypted-variables
[has nothing to do with _building package distributions_]:
https://github.com/pypa/gh-action-pypi-publish/issues/11#issuecomment-530480449
