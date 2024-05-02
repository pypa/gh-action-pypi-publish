import logging
import os
import sys
from pathlib import Path
from typing import NoReturn

from pypi_attestation_models import AttestationPayload
from sigstore.oidc import IdentityError, IdentityToken, detect_credential
from sigstore.sign import Signer, SigningContext

# Be very verbose.
sigstore_logger = logging.getLogger("sigstore")
sigstore_logger.setLevel(logging.DEBUG)
sigstore_logger.addHandler(logging.StreamHandler())

_GITHUB_STEP_SUMMARY = Path(os.getenv("GITHUB_STEP_SUMMARY"))

# The top-level error message that gets rendered.
# This message wraps one of the other templates/messages defined below.
_ERROR_SUMMARY_MESSAGE = """
Attestation generation failure:

{message}

You're seeing this because the action attempted to generated PEP 740
attestations for its inputs, but failed to do so.
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


def die(msg: str) -> NoReturn:
    with _GITHUB_STEP_SUMMARY.open("a", encoding="utf-8") as io:
        print(_ERROR_SUMMARY_MESSAGE.format(message=msg), file=io)

    # HACK: GitHub Actions' annotations don't work across multiple lines naively;
    # translating `\n` into `%0A` (i.e., HTML percent-encoding) is known to work.
    # See: https://github.com/actions/toolkit/issues/193
    msg = msg.replace("\n", "%0A")
    print(f"::error::Attestation generation failure: {msg}", file=sys.stderr)
    sys.exit(1)


def debug(msg: str):
    print(f"::debug::{msg}", file=sys.stderr)


# pylint: disable=redefined-outer-name
def attest_dist(dist: Path, signer: Signer) -> None:
    # We are the publishing step, so there should be no pre-existing publish
    # attestation. The presence of one indicates user confusion.
    attestation_path = Path(f"{dist}.publish.attestation")
    if attestation_path.is_file():
        die(f"{dist} already has a publish attestation: {attestation_path}")

    payload = AttestationPayload.from_dist(dist)
    attestation = payload.sign(signer)

    attestation_path.write_text(attestation.model_dump_json(), encoding="utf-8")
    debug(f"saved publish attestation: {dist=} {attestation_path=}")


packages_dir = Path(sys.argv[1])

try:
    # NOTE: audience is always sigstore.
    oidc_token = detect_credential()
    identity = IdentityToken(oidc_token)
except IdentityError as identity_error:
    # NOTE: We only perform attestations in trusted publishing flows, so we
    # don't need to re-check for the "PR from fork" error mode, only
    # generic token retrieval errors.
    cause = _TOKEN_RETRIEVAL_FAILED_MESSAGE.format(identity_error=identity_error)
    die(cause)

# Collect all sdists and wheels.
dists = [sdist.absolute() for sdist in packages_dir.glob("*.tar.gz")]
dists.extend(whl.absolute() for whl in packages_dir.glob("*.whl"))

with SigningContext.production().signer(identity, cache=True) as signer:
    for dist in dists:
        # This should never really happen, but some versions of GitHub's
        # download-artifact will create a subdirectory with the same name
        # as the artifact being downloaded, e.g. `dist/foo.whl/foo.whl`.
        if not dist.is_file():
            die(f"Path looks like a distribution but is not a file: {dist}")

        attest_dist(dist, signer)
