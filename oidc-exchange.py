import base64
import json
import os
import sys
from http import HTTPStatus
from pathlib import Path
from typing import NoReturn
from urllib.parse import urlparse

import id  # pylint: disable=redefined-builtin
import requests

_GITHUB_STEP_SUMMARY = Path(os.getenv("GITHUB_STEP_SUMMARY"))

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
"""

# Rendered if the package index refuses the given OIDC token.
_SERVER_REFUSED_TOKEN_EXCHANGE_MESSAGE = """
Token request failed: the server refused the request for the following reasons:

{reasons}

This generally indicates a trusted publisher configuration error, but could
also indicate an internal error on GitHub or PyPI's part.

{rendered_claims}
"""

_RENDERED_CLAIMS = """
The claims rendered below are **for debugging purposes only**. You should **not**
use them to configure a trusted publisher unless they already match your expectations.

If a claim is not present in the claim set, then it is rendered as `MISSING`.

* `sub`: `{sub}`
* `repository`: `{repository}`
* `repository_owner`: `{repository_owner}`
* `repository_owner_id`: `{repository_owner_id}`
* `job_workflow_ref`: `{job_workflow_ref}`
* `ref`: `{ref}`
"""

# Rendered if the package index's token response isn't valid JSON.
_SERVER_TOKEN_RESPONSE_MALFORMED_JSON = """
Token request failed: the index produced an unexpected
{status_code} response.

This strongly suggests a server configuration or downtime issue; wait
a few minutes and try again.
"""

# Rendered if the package index's token response isn't a valid API token payload.
_SERVER_TOKEN_RESPONSE_MALFORMED_MESSAGE = """
Token response error: the index gave us an invalid response.

This strongly suggests a server configuration or downtime issue; wait
a few minutes and try again.
"""


def die(msg: str) -> NoReturn:
    with _GITHUB_STEP_SUMMARY.open("a", encoding="utf-8") as io:
        print(_ERROR_SUMMARY_MESSAGE.format(message=msg), file=io)

    # HACK: GitHub Actions' annotations don't work across multiple lines naively;
    # translating `\n` into `%0A` (i.e., HTML percent-encoding) is known to work.
    # See: https://github.com/actions/toolkit/issues/193
    msg = msg.replace("\n", "%0A")
    print(f"::error::Trusted publishing exchange failure: {msg}", file=sys.stderr)
    sys.exit(1)


def debug(msg: str):
    print(f"::debug::{msg.title()}", file=sys.stderr)


def get_normalized_input(name: str) -> str | None:
    name = f"INPUT_{name.upper()}"
    if val := os.getenv(name):
        return val
    return os.getenv(name.replace("-", "_"))


def assert_successful_audience_call(resp: requests.Response, domain: str):
    if resp.ok:
        return

    match resp.status_code:
        case HTTPStatus.FORBIDDEN:
            # This index supports OIDC, but forbids the client from using
            # it (either because it's disabled, ratelimited, etc.)
            die(
                f"audience retrieval failed: repository at {domain} has trusted publishing disabled",
            )
        case HTTPStatus.NOT_FOUND:
            # This index does not support OIDC.
            die(
                "audience retrieval failed: repository at "
                f"{domain} does not indicate trusted publishing support",
            )
        case other:
            status = HTTPStatus(other)
            # Unknown: the index may or may not support OIDC, but didn't respond with
            # something we expect. This can happen if the index is broken, in maintenance mode,
            # misconfigured, etc.
            die(
                "audience retrieval failed: repository at "
                f"{domain} responded with unexpected {other}: {status.phrase}",
            )


def render_claims(token: str) -> str:
    _, payload, _ = token.split(".", 2)

    # urlsafe_b64decode needs padding; JWT payloads don't contain any.
    payload += "=" * (4 - (len(payload) % 4))
    claims = json.loads(base64.urlsafe_b64decode(payload))

    def _get(name: str) -> str:  # noqa: WPS430
        return claims.get(name, "MISSING")

    return _RENDERED_CLAIMS.format(
        sub=_get("sub"),
        repository=_get("repository"),
        repository_owner=_get("repository_owner"),
        repository_owner_id=_get("repository_owner_id"),
        job_workflow_ref=_get("job_workflow_ref"),
        ref=_get("ref"),
    )


repository_url = get_normalized_input("repository-url")
repository_domain = urlparse(repository_url).netloc
token_exchange_url = f"https://{repository_domain}/_/oidc/github/mint-token"

# Indices are expected to support `https://{domain}/_/oidc/audience`,
# which tells OIDC exchange clients which audience to use.
audience_url = f"https://{repository_domain}/_/oidc/audience"
audience_resp = requests.get(audience_url)
assert_successful_audience_call(audience_resp, repository_domain)

oidc_audience = audience_resp.json()["audience"]

debug(f"selected trusted publishing exchange endpoint: {token_exchange_url}")

try:
    oidc_token = id.detect_credential(audience=oidc_audience)
except id.IdentityError as identity_error:
    die(_TOKEN_RETRIEVAL_FAILED_MESSAGE.format(identity_error=identity_error))

# Now we can do the actual token exchange.
mint_token_resp = requests.post(
    token_exchange_url,
    json={"token": oidc_token},
)

try:
    mint_token_payload = mint_token_resp.json()
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
    reasons = "\n".join(
        f"* `{error['code']}`: {error['description']}"
        for error in mint_token_payload["errors"]
    )

    rendered_claims = render_claims(oidc_token)

    die(
        _SERVER_REFUSED_TOKEN_EXCHANGE_MESSAGE.format(
            reasons=reasons,
            rendered_claims=rendered_claims,
        ),
    )

pypi_token = mint_token_payload.get("token")
if pypi_token is None:
    die(_SERVER_TOKEN_RESPONSE_MALFORMED_MESSAGE)

# Mask the newly minted PyPI token, so that we don't accidentally leak it in logs.
print(f"::add-mask::{pypi_token}", file=sys.stderr)

# This final print will be captured by the subshell in `twine-upload.sh`.
print(pypi_token)
