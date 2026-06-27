import json
import os
import pathlib

DESCRIPTION = 'description'
REQUIRED = 'required'

REF = os.environ['REF']
REPO = os.environ['REPO']
REPO_ID = os.environ['REPO_ID']
REPO_ID_GH_ACTION = '178055147'

ACTION_SHELL_CHECKOUT_PATH = pathlib.Path(__file__).parent.resolve()


def set_image(ref: str, repo: str, repo_id: str) -> str:
    if repo_id == REPO_ID_GH_ACTION:
        return str(ACTION_SHELL_CHECKOUT_PATH / 'Dockerfile')
    docker_ref = ref.replace('/', '-')
    return f'docker://ghcr.io/{repo}:{docker_ref}'


image = set_image(REF, REPO, REPO_ID)

action = {
    'name': '🏃',
    DESCRIPTION: (
        'Run Docker container to upload Python distribution packages to PyPI'
    ),
    'inputs': {
        'user': {DESCRIPTION: 'PyPI user', REQUIRED: False},
        'password': {
            DESCRIPTION: 'Password for your PyPI user or an access token',
            REQUIRED: False,
        },
        'repository-url': {
            DESCRIPTION: 'The repository URL to use',
            REQUIRED: False,
        },
        'packages-dir': {
            DESCRIPTION: 'The target directory for distribution',
            REQUIRED: False,
        },
        'verify-metadata': {
            DESCRIPTION: 'Check metadata before uploading',
            REQUIRED: False,
        },
        'skip-existing': {
            DESCRIPTION: (
                'Do not fail if a Python package distribution'
                ' exists in the target package index'
            ),
            REQUIRED: False,
        },
        'verbose': {DESCRIPTION: 'Show verbose output.', REQUIRED: False},
        'print-hash': {
            DESCRIPTION: 'Show hash values of files to be uploaded',
            REQUIRED: False,
        },
        'attestations': {
            DESCRIPTION: (
                ' Enable support for PEP 740 attestations.'
                ' Only works with PyPI and TestPyPI via Trusted Publishing.'
            ),
            REQUIRED: False,
        },
    },
    'runs': {
        'using': 'docker',
        'image': image,
    },
}

# The generated trampoline action must exist in the allowlisted
# runner-defined working directory so it can be referenced by the
# relative path starting with `./`.
#
# This mutates the end-user's workspace slightly but uses a path
# that is unlikely to clash with somebody else's use.
#
# We cannot use randomized paths because the composite action
# syntax does not allow accessing variables in `uses:`. This
# means that we end up having to hardcode this path both here and
# in `action.yml`.
action_path = pathlib.Path(
    '.github/.tmp/.generated-actions/'
    'run-pypi-publish-in-docker-container/action.yml',
)
action_path.parent.mkdir(parents=True, exist_ok=True)
action_path.write_text(json.dumps(action, ensure_ascii=False), encoding='utf-8')
