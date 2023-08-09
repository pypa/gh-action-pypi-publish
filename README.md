[![SWUbanner]][SWUdocs]

[![🧪 GitHub Actions CI/CD workflow tests badge]][GHA workflow runs list]
[![pre-commit.ci status badge]][pre-commit.ci results page]

# PyPI publish GitHub Action

This action allows you to upload your [Python distribution packages]
in the `dist/` directory to PyPI.
This text suggests a minimalistic usage overview. For more detailed
walkthrough check out the [PyPA guide].

If you have any feedback regarding specific action versions, please leave
comments in the corresponding [per-release announcement discussions].


## 🌇 `master` branch sunset ❗

The `master` branch version has been sunset. Please, change the GitHub
Action version you use from `master` to `release/v1` or use an exact
tag, or opt-in to [use a full Git commit SHA] and Dependabot.


## Usage

### Trusted publishing

> [!NOTE]
> Trusted publishing is sometimes referred to by its
> underlying technology -- OpenID Connect, or OIDC for short.
> If you see references to "OIDC publishing" in the context of PyPI,
> this is what they're referring to.

This example jumps right into the current best practice. If you want to
use API tokens directly or a less secure username and password, check out
[how to specify username and password].

This action supports PyPI's [trusted publishing]
implementation, which allows authentication to PyPI without a manually
configured API token or username/password combination. To perform
[trusted publishing] with this action, your project's
publisher must already be configured on PyPI.

To enter the trusted publishing flow, configure this action's job with the
`id-token: write` permission and **without** an explicit username or password:

```yaml
# .github/workflows/ci-cd.yml
jobs:
  pypi-publish:
    name: Upload release to PyPI
    runs-on: ubuntu-latest
    environment:
      name: pypi
      url: https://pypi.org/p/<your-pypi-project-name>
    permissions:
      id-token: write  # IMPORTANT: this permission is mandatory for trusted publishing
    steps:
    # retrieve your distributions here

    - name: Publish package distributions to PyPI
      uses: pypa/gh-action-pypi-publish@release/v1
```

> [!NOTE]
> Instead of using branch pointers, like `unstable/v1`, pin versions of Actions
> that you use to tagged versions or sha1 commit identifiers.
> This will make your workflows more secure and better reproducible, saving you
> from sudden and unpleasant surprises.

Other indices that support trusted publishing can also be used, like TestPyPI:

```yaml
- name: Publish package distributions to TestPyPI
  uses: pypa/gh-action-pypi-publish@release/v1
  with:
    repository-url: https://test.pypi.org/legacy/
```
_(don't forget to update the environment name to `testpypi` or similar!)_

> [!NOTE]
> Only set the `id-token: write` permission in the job that does
> publishing, not globally. Also, try to separate building from publishing
> — this makes sure that any scripts maliciously injected into the build
> or test environment won't be able to elevate privileges while flying under
> the radar.

A common use case is to upload packages only on a tagged commit, to do so add a
filter to the job:

```yml
    if: github.event_name == 'push' && startsWith(github.ref, 'refs/tags')
```


## Non-goals

This GitHub Action [has nothing to do with _building package
distributions_]. Users are responsible for preparing dists for upload
by putting them into the `dist/` folder prior to running this Action.

> [!IMPORTANT]
> Since this GitHub Action is docker-based, it can only
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

For example, you could implement a parallel job that
pushes every commit to TestPyPI or your own index server,
like `devpi`. For this, you'd need to (1) specify a custom
`repository-url` value and (2) generate a unique version
number for each upload so that they'd not create a conflict.
The latter is possible if you use `setuptools_scm` package but
you could also invent your own solution based on the distance
to the latest tagged commit.

You'll need to create another token for a separate host and then [save it as a
GitHub repo secret][Creating & using secrets] under an environment used in
your job. Though, passing a password would disable the secretless [trusted
publishing] so it's better to configure it instead, when publishing to TestPyPI
and not something custom.

The action invocation in this case would look like:
```yml
- name: Publish package to TestPyPI
  uses: pypa/gh-action-pypi-publish@release/v1
  with:
    password: ${{ secrets.TEST_PYPI_API_TOKEN }}
    repository-url: https://test.pypi.org/legacy/
```

### Customizing target package dists directory

You can change the default target directory of `dist/`
to any directory of your liking. The action invocation
would now look like:

```yml
- name: Publish package to PyPI
  uses: pypa/gh-action-pypi-publish@release/v1
  with:
    packages-dir: custom-dir/
```

### Disabling metadata verification

It is recommended that you run `twine check` just after producing your files,
but this also runs `twine check` before upload. You can also disable the twine
check with:

```yml
   with:
     verify-metadata: false
```

### Tolerating release package file duplicates

Sometimes, when you publish releases from multiple places, your workflow
may hit race conditions. For example, when publishing from multiple CIs
or even having workflows with the same steps triggered within GitHub
Actions CI/CD for different events concerning the same high-level act.

To facilitate this use-case, you may use `skip-existing` (disabled by
default) setting as follows:

```yml
   with:
     skip-existing: true
```

> [!NOTE]
> Try to avoid enabling this setting where possible. If you
> have steps for publishing to both PyPI and TestPyPI, consider only using
> it for the latter, having the former fail loudly on duplicates.

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
    print-hash: true
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

The secret used in `${{ secrets.DEVPI_PASSWORD }}` needs to be created on the
environment page under the settings of your project on GitHub.
See [Creating & using secrets].

In the past, when publishing to PyPI, the most secure way of the access scoping
for automatic publishing was to use the [API tokens][PyPI API token] feature of
PyPI. One would make it project-scoped and save as an environment-bound secret
in their GitHub repository settings, naming it `${{ secrets.PYPI_API_TOKEN }}`,
for example. See [Creating & using secrets]. While still secure,
[trusted publishing] is now encouraged over API tokens as a best practice
on supported platforms (like GitHub).

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

[use a full Git commit SHA]:
https://julienrenaux.fr/2019/12/20/github-actions-security-risk/

[per-release announcement discussions]:
https://github.com/pypa/gh-action-pypi-publish/discussions/categories/announcements

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

[warehouse#12965]: https://github.com/pypi/warehouse/issues/12965
[trusted publishing]: https://docs.pypi.org/trusted-publishers/

[how to specify username and password]: #specifying-a-different-username
