# PyPI publish GitHub Action
This action allows you to upload your [Python distribution package](
https://packaging.python.org/glossary/#term-distribution-package) to
PyPI.
This text suggests a minimalistic usage overview. For more detailed
walkthrough check out the [PyPA guide].


## Usage

To use the action add the following step to your workflow file (e.g.
`.github/workflows/main.yml`)


```yml
- name: Publish a Python distribution to PyPI
  uses: pypa/gh-action-pypi-publish@master
  with:
    user: __token__
    password: ${{ secrets.pypi_password }}
```

> **Pro tip**: instead of using branch pointers, like `master`, pin versions of
Actions that you use to tagged versions or sha1 commit identifiers. This will
make your workflows more secure and better reproducible, saving you from sudden
and unpleasant surprises.

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

The secret used in `${{ secrets.pypi_password }}` needs to be created on the
settings page of your project on GitHub. See [Creating & using secrets].


## Non-goals

This GitHub Action [has nothing to do with _building package
distributions_]. Users are responsible for preparing dists for upload
by putting them into the `dist/` folder prior to running this Action.


## Advanced release management

For best results, figure out what kind of workflow fits your
project's specific needs.

For example, you could implement a parallel workflow that
pushes every commit to TestPyPI or your own index server,
like `devpi`. For this, you'd need to (1) specify a custom
`repository_url` value and (2) generate a unique version
number for each upload so that they'd not create a conflict.
The latter is possible if you use `setuptools_scm` package but
you could also invent your own solution based on the distance
to the latest tagged commit.

You'll need to create another token for a separate host and then
[save it as a GitHub repo secret][Creating & using secrets].

The action invocation in this case would look like:
```yml
- name: Publish package to TestPyPI
  uses: pypa/gh-action-pypi-publish@master
  with:
    user: __token__
    password: ${{ secrets.test_pypi_password }}
    repository_url: https://test.pypi.org/legacy/
```


## License

The Dockerfile and associated scripts and documentation in this project
are released under the [BSD 3-clause license](LICENSE.md).


[Creating & using secrets]:
https://help.github.com/en/actions/automating-your-workflow-with-github-actions/creating-and-using-encrypted-secrets
[has nothing to do with _building package distributions_]:
https://github.com/pypa/gh-action-pypi-publish/issues/11#issuecomment-530480449
[PyPA guide]:
https://packaging.python.org/guides/publishing-package-distribution-releases-using-github-actions-ci-cd-workflows/
