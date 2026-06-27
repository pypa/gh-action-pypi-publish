import base64
import json
import os
import sys
import typing as t
from http import HTTPStatus
from pathlib import Path
from urllib.parse import urlparse

import id  # pylint: disable=redefined-builtin
import requests

_GITHUB_STEP_SUMMARY = Path(os.environ['GITHUB_STEP_SUMMARY'])

# The top-level error message that gets rendered.
# This message wraps one of the other templates/messages defined below.
_ERROR_SUMMARY_MESSAGE = """
Trusted publishing exchange failure:

{message}

You're seeing this because the action wasn't given the inputs needed to
perform password-based or token-based authentication. If you intended to
perform one of those authentication methods instead of trusted
publishing, then you should double-check your secret configuration and variable
names.

Read more about trusted publishers at https://docs.pypi.org/trusted-publishers/

Read more about how this action uses trusted publishers at
https://github.com/marketplace/actions/pypi-publish#trusted-publishing
"""

# Rendered if OIDC identity token retrieval fails for any reason.
_TOKEN_RETRIEVAL_FAILED_MESSAGE = """
OpenID Connect token retrieval failed: {identity_error}

This generally indicates a workflow configuration error, such as insufficient
permissions. Make sure that your workflow has `id-token: write` configured
at the job level, e.g.:

```yaml
permissions:
  id-token: write
```

Learn more at https://docs.github.com/en/actions/deployment/security-hardening-your-deployments/about-security-hardening-with-openid-connect#adding-permissions-settings.
"""  # noqa: S105; not a password

# Specialization of the token retrieval failure case, when we know that
# the failure cause is use within a third-party PR.
_TOKEN_RETRIEVAL_FAILED_FORK_PR_MESSAGE = """
OpenID Connect token retrieval failed: {identity_error}

The workflow context indicates that this action was called from a
pull request on a fork. GitHub doesn't give these workflows OIDC permissions,
even if `id-token: write` is explicitly configured.

To fix this, change your publishing workflow to use an event that
forks of your repository cannot trigger (such as tag or release
creation, or a manually triggered workflow dispatch).
"""  # noqa: S105; not a password

# Rendered if the package index refuses the given OIDC token.
_SERVER_REFUSED_TOKEN_EXCHANGE_MESSAGE = """
Token request failed: the server refused the request for the following reasons:

{reasons}

This generally indicates a trusted publisher configuration error, but could
also indicate an internal error on GitHub or PyPI's part.

{rendered_claims}
"""  # noqa: S105; not a password

_RENDERED_CLAIMS = """
The claims rendered below are **for debugging purposes only**. You should **not**
use them to configure a trusted publisher unless they already match your expectations.

If a claim is not present in the claim set, then it is rendered as `MISSING`.

* `sub`: `{sub}`
* `repository`: `{repository}`
* `repository_owner`: `{repository_owner}`
* `repository_owner_id`: `{repository_owner_id}`
* `workflow_ref`: `{workflow_ref}`
* `job_workflow_ref`: `{job_workflow_ref}`
* `ref`: `{ref}`
* `environment`: `{environment}`

See https://docs.pypi.org/trusted-publishers/troubleshooting/ for more help.
"""

_REUSABLE_WORKFLOW_WARNING = """
The claims in this token suggest that the calling workflow is a reusable workflow.

In particular, this action was initiated by:

    {job_workflow_ref}

Whereas its parent workflow is:

    {workflow_ref}

Reusable workflows are **not currently supported** by PyPI's Trusted Publishing
functionality, and are subject to breakage. Users are **strongly encouraged**
to avoid using reusable workflows for Trusted Publishing until support
becomes official. Please, do not report bugs if this breaks.

For more information, see:

* https://docs.pypi.org/trusted-publishers/troubleshooting/#reusable-workflows-on-github
* https://github.com/pypa/gh-action-pypi-publish/issues/166 — subscribe to
  this issue to watch the progress and learn when reusable workflows become
  supported officially
"""

# Rendered if the package index's token response isn't valid JSON.
_SERVER_TOKEN_RESPONSE_MALFORMED_JSON = """
Token request failed: the index produced an unexpected
{status_code} response.

This strongly suggests a server configuration or downtime issue; wait
a few minutes and try again.

You can monitor PyPI's status here: https://status.python.org/
"""  # noqa: S105; not a password

# Rendered if the package index's token response isn't a valid API token payload.
_SERVER_TOKEN_RESPONSE_MALFORMED_MESSAGE = """
Token response error: the index gave us an invalid response.

This strongly suggests a server configuration or downtime issue; wait
a few minutes and try again.
"""  # noqa: S105; not a password


class TrustedPublishingClaims(t.TypedDict):
    sub: str
    repository: str
    repository_owner: str
    repository_owner_id: str
    workflow_ref: str
    job_workflow_ref: str
    ref: str
    environment: str


class PullRequestRepoGitHubEventObject(t.TypedDict):
    fork: bool


class PullRequestHeadGitHubEventObject(t.TypedDict):
    repo: PullRequestRepoGitHubEventObject


class PullRequestGitHubEventObject(t.TypedDict):
    head: PullRequestHeadGitHubEventObject


class ThirdPartyPullRequestGitHubEvent(t.TypedDict):
    pull_request: PullRequestGitHubEventObject


class TrustedPublishingAudience(t.TypedDict):
    audience: str


class TrustedPublishingTokenRetrievalError(t.TypedDict):
    code: str
    description: str


class TrustedPublishingToken(t.TypedDict):
    message: str
    errors: list[TrustedPublishingTokenRetrievalError]
    token: str
    success: bool
    expires: int


def die(msg: str) -> t.NoReturn:
    with _GITHUB_STEP_SUMMARY.open('a', encoding='utf-8') as io:
        print(_ERROR_SUMMARY_MESSAGE.format(message=msg), file=io)

    # HACK: GitHub Actions' annotations don't work across multiple lines naively;
    # translating `\n` into `%0A` (i.e., HTML percent-encoding) is known to work.
    # See: https://github.com/actions/toolkit/issues/193
    msg = msg.replace('\n', '%0A')
    print(f'::error::Trusted publishing exchange failure: {msg}', file=sys.stderr)
    sys.exit(1)


def warn(msg: str) -> None:
    with _GITHUB_STEP_SUMMARY.open('a', encoding='utf-8') as io:
        print(msg, file=io)

    msg = msg.replace('\n', '%0A')
    print(f'::warning::Potential workflow misconfiguration: {msg}', file=sys.stderr)


def debug(msg: str) -> None:
    print(f'::debug::{msg.title()}', file=sys.stderr)


def get_normalized_input(name: str) -> str | None:
    name = f'INPUT_{name.upper()}'
    if val := os.getenv(name):
        return val
    return os.getenv(name.replace('-', '_'))


def assert_successful_audience_call(resp: requests.Response, domain: str) -> None:
    if resp.ok:
        return

    match resp.status_code:
        case HTTPStatus.FORBIDDEN:
            # This index supports OIDC, but forbids the client from using
            # it (either because it's disabled, ratelimited, etc.)
            die(
                f'audience retrieval failed: repository at {domain} has trusted publishing disabled',
            )
        case HTTPStatus.NOT_FOUND:
            # This index does not support OIDC.
            die(
                'audience retrieval failed: repository at '
                f'{domain} does not indicate trusted publishing support',
            )
        case other:
            status = HTTPStatus(other)
            # Unknown: the index may or may not support OIDC, but didn't respond with
            # something we expect. This can happen if the index is broken, in maintenance mode,
            # misconfigured, etc.
            die(
                'audience retrieval failed: repository at '
                f'{domain} responded with unexpected {other}: {status.phrase}',
            )


def extract_claims(token: str) -> TrustedPublishingClaims:
    _, payload, _ = token.split('.', 2)

    # urlsafe_b64decode needs padding; JWT payloads don't contain any.
    payload += '=' * (4 - (len(payload) % 4))

    claims: TrustedPublishingClaims = json.loads(
        base64.urlsafe_b64decode(payload),
    )
    return claims


def render_claims(claims: TrustedPublishingClaims) -> str:
    def _get(name: str) -> str:  # noqa: WPS430
        return str(claims.get(name, 'MISSING'))

    return _RENDERED_CLAIMS.format(
        sub=_get('sub'),
        repository=_get('repository'),
        repository_owner=_get('repository_owner'),
        repository_owner_id=_get('repository_owner_id'),
        workflow_ref=_get('workflow_ref'),
        job_workflow_ref=_get('job_workflow_ref'),
        ref=_get('ref'),
        environment=_get('environment'),
    )


def warn_on_reusable_workflow(claims: TrustedPublishingClaims) -> None:
    # A reusable workflow is identified by having different values
    # for its workflow_ref (the initiating workflow) and job_workflow_ref
    # (the reusable workflow).
    workflow_ref = claims.get('workflow_ref')
    job_workflow_ref = claims.get('job_workflow_ref')

    if workflow_ref == job_workflow_ref:
        return

    warn(
        _REUSABLE_WORKFLOW_WARNING.format(
            workflow_ref=workflow_ref, job_workflow_ref=job_workflow_ref,
        ),
    )


def event_is_third_party_pr() -> bool:
    # Non-`pull_request` events cannot be from third-party PRs.
    if os.getenv('GITHUB_EVENT_NAME') != 'pull_request':
        return False

    event_path = os.getenv('GITHUB_EVENT_PATH')
    if not event_path:
        # No GITHUB_EVENT_PATH indicates a weird GitHub or runner bug.
        debug('unexpected: no GITHUB_EVENT_PATH to check')
        return False

    try:
        event: ThirdPartyPullRequestGitHubEvent = json.loads(
            Path(event_path).read_bytes(),
        )
    except json.JSONDecodeError:
        debug('unexpected: GITHUB_EVENT_PATH does not contain valid JSON')
        return False

    try:
        return event['pull_request']['head']['repo']['fork']
    except KeyError:
        return False


def _detect_credential(audience: str, /) -> str:
    token = id.detect_credential(audience=audience)
    if token is None:
        raise id.IdentityError(
            'Attempted to discover OIDC in broken environment',
        )
    return token


repository_url = get_normalized_input('repository-url')
repository_domain = str(urlparse(repository_url).netloc)
token_exchange_url = f'https://{repository_domain}/_/oidc/mint-token'

# Indices are expected to support `https://{domain}/_/oidc/audience`,
# which tells OIDC exchange clients which audience to use.
audience_url = f'https://{repository_domain}/_/oidc/audience'
audience_resp = requests.get(audience_url, timeout=5)  # S113 wants a timeout
assert_successful_audience_call(audience_resp, repository_domain)


oidc_audience_resp: TrustedPublishingAudience = audience_resp.json()
oidc_audience = oidc_audience_resp['audience']

debug(f'selected trusted publishing exchange endpoint: {token_exchange_url}')


try:
    oidc_token = _detect_credential(oidc_audience)
except id.IdentityError as identity_error:
    cause_msg_tmpl = (
        _TOKEN_RETRIEVAL_FAILED_FORK_PR_MESSAGE
        if event_is_third_party_pr()
        else _TOKEN_RETRIEVAL_FAILED_MESSAGE
    )
    for_cause_msg = cause_msg_tmpl.format(identity_error=identity_error)
    die(for_cause_msg)


# Perform a non-fatal check to see if we're running on a reusable
# workflow, and emit a warning if so.
oidc_claims = extract_claims(oidc_token)
warn_on_reusable_workflow(oidc_claims)

oidc_token_payload: dict[str, str] = {'token': oidc_token}
# Now we can do the actual token exchange.
mint_token_resp = requests.post(
    token_exchange_url,
    json=oidc_token_payload,
    timeout=5,  # S113 wants a timeout
)


try:
    mint_token_payload: TrustedPublishingToken = mint_token_resp.json()
except requests.JSONDecodeError:
    # Token exchange failure normally produces a JSON error response, but
    # we might have hit a server error instead.
    die(
        _SERVER_TOKEN_RESPONSE_MALFORMED_JSON.format(
            status_code=mint_token_resp.status_code,
        ),
    )

# On failure, the JSON response includes the list of errors that
# occurred during minting.
if not mint_token_resp.ok:
    reasons = '\n'.join(
        f'* `{error["code"]}`: {error["description"]}'
        for error in mint_token_payload['errors']
    )

    rendered_claims = render_claims(oidc_claims)

    die(
        _SERVER_REFUSED_TOKEN_EXCHANGE_MESSAGE.format(
            reasons=reasons,
            rendered_claims=rendered_claims,
        ),
    )

pypi_token = mint_token_payload.get('token')
if pypi_token is None:
    die(_SERVER_TOKEN_RESPONSE_MALFORMED_MESSAGE)

# Mask the newly minted PyPI token, so that we don't accidentally leak it in logs.
print(f'::add-mask::{pypi_token}', file=sys.stderr)

# This final print will be captured by the subshell in `twine-upload.sh`.
print(pypi_token)
