[![SWUbanner]][SWUdocs]

[![🧪 GitHub Actions CI/CD workflow tests badge]][GHA workflow runs list]
[![pre-commit.ci status badge]][pre-commit.ci results page]

# PyPI publish GitHub Action

This action allows you to upload your [Python distribution packages]
in the `dist/` directory to PyPI.
This text suggests a minimalistic usage overview. For more detailed
walkthrough check out the [PyPA guide].


## 🌇 `master` branch sunset ❗

The `master` branch version has been sunset. Please, change the GitHub
Action version you use from `master` to `release/v1` or use an exact
tag, or a full Git commit SHA.


## Usage

To use the action add the following step to your workflow file (e.g.
`.github/workflows/main.yml`)


```yml
- name: Publish a Python distribution to PyPI
  uses: pypa/gh-action-pypi-publish@release/v1
  with:
    password: ${{ secrets.PYPI_API_TOKEN }}
```

> **Pro tip**: instead of using branch pointers, like `unstable/v1`, pin
versions of Actions that you use to tagged versions or sha1 commit identifiers.
This will make your workflows more secure and better reproducible, saving you
from sudden and unpleasant surprises.

A common use case is to upload packages only on a tagged commit, to do so add a
filter to the step:


```yml
  if: github.event_name == 'push' && startsWith(github.ref, 'refs/tags')
```

So the full step would look like:


```yml
- name: Publish package
  if: github.event_name == 'push' && startsWith(github.ref, 'refs/tags')
  uses: pypa/gh-action-pypi-publish@release/v1
  with:
    password: ${{ secrets.PYPI_API_TOKEN }}
```

The example above uses the new [API token][PyPI API token] feature of
PyPI, which is recommended to restrict the access the action has.

The secret used in `${{ secrets.PYPI_API_TOKEN }}` needs to be created on the
settings page of your project on GitHub. See [Creating & using secrets].


## Non-goals

This GitHub Action [has nothing to do with _building package
distributions_]. Users are responsible for preparing dists for upload
by putting them into the `dist/` folder prior to running this Action.

> **IMPORTANT**: Since this GitHub Action is docker-based, it can only
> be used from within GNU/Linux based jobs in GitHub Actions CI/CD
> workflows. This is by design and is unlikely to change due to a number
> of considerations we rely on.
>
> This should not stop one from publishing platform-specific
> distribution packages, though. It is strongly advised to separate jobs
> for building the OS-specific wheels from the publish job. This allows
> one to (1) test exactly the same artifacts that are about to be
> uploaded to PyPI, (2) prevent parallel unsynchronized jobs from
> publishing only part of the dists asynchronously (in case when part of
> the jobs fail and others succeed ending up with an incomplete release
> on PyPI) and (3) make an atomic upload to PyPI (when part of the dists
> appear on PyPI, installers like pip will use that version for the
> dependency resolution but this may cause some environments to use
> sdists while the wheel for their runtime is not yet available).
>
> To implement this sort of orchestration, please use
> `actions/upload-artifact` and `actions/download-artifact` actions for
> sharing the built dists across stages and jobs. Then, use the `needs`
> setting to order the build, test and publish stages.


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
  uses: pypa/gh-action-pypi-publish@release/v1
  with:
    password: ${{ secrets.TEST_PYPI_API_TOKEN }}
    repository_url: https://test.pypi.org/legacy/
```

### Customizing target package dists directory

You can change the default target directory of `dist/`
to any directory of your liking. The action invocation
would now look like:

```yml
- name: Publish package to PyPI
  uses: pypa/gh-action-pypi-publish@release/v1
  with:
    password: ${{ secrets.PYPI_API_TOKEN }}
    packages_dir: custom-dir/
```

### Disabling metadata verification

It is recommended that you run `twine check` just after producing your files,
but this also runs `twine check` before upload. You can also disable the twine
check with:

```yml
   with:
     verify_metadata: false
```

### Tolerating release package file duplicates

Sometimes, when you publish releases from multiple places, your workflow
may hit race conditions. For example, when publishing from multiple CIs
or even having workflows with the same steps triggered within GitHub
Actions CI/CD for different events concerning the same high-level act.

To facilitate this use-case, you may use `skip_existing` (disabled by
default) setting as follows:

```yml
   with:
     skip_existing: true
```

> **Pro tip**: try to avoid enabling this setting where possible. If you
have steps for publishing to both PyPI and TestPyPI, consider only using
it for the latter, having the former fail loudly on duplicates.

### For Debugging

Sometimes, `twine upload` can fail and to debug use the `verbose` setting as follows:

```yml
   with:
     verbose: true
```

### Showing hash values of files to be uploaded

You may want to verify whether the files on PyPI were automatically uploaded by CI script.
It will show SHA256, MD5, BLAKE2-256 values of files to be uploaded.

```yml
  with:
    print_hash: true
```

### Specifying a different username

The default username value is `__token__`. If you publish to a custom
registry that does not provide API tokens, like `devpi`, you may need to
specify a custom username and password pair. This is how it's done.

```yml
  with:
    user: guido
    password: ${{ secrets.DEVPI_PASSWORD }}
```

## License

The Dockerfile and associated scripts and documentation in this project
are released under the [BSD 3-clause license](LICENSE.md).


[🧪 GitHub Actions CI/CD workflow tests badge]:
https://github.com/pypa/gh-action-pypi-publish/actions/workflows/self-smoke-test-action.yml/badge.svg?branch=unstable%2Fv1&event=push
[GHA workflow runs list]:
https://github.com/pypa/gh-action-pypi-publish/actions/workflows/self-smoke-test-action.yml?query=branch%3Aunstable%2Fv1

[pre-commit.ci results page]:
https://results.pre-commit.ci/latest/github/pypa/gh-action-pypi-publish/unstable/v1
[pre-commit.ci status badge]:
https://results.pre-commit.ci/badge/github/pypa/gh-action-pypi-publish/unstable/v1.svg

[Creating & using secrets]:
https://help.github.com/en/actions/automating-your-workflow-with-github-actions/creating-and-using-encrypted-secrets
[has nothing to do with _building package distributions_]:
https://github.com/pypa/gh-action-pypi-publish/issues/11#issuecomment-530480449
[PyPA guide]:
https://packaging.python.org/guides/publishing-package-distribution-releases-using-github-actions-ci-cd-workflows/
[PyPI API token]: https://pypi.org/help/#apitoken
[Python distribution packages]:
https://packaging.python.org/glossary/#term-Distribution-Package
[SWUbanner]:
https://raw.githubusercontent.com/vshymanskyy/StandWithUkraine/main/banner-direct-single.svg
[SWUdocs]:
https://github.com/vshymanskyy/StandWithUkraine/blob/main/docs/README.md
