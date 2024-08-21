import logging
import os
import sys
from pathlib import Path
from typing import NoReturn

from pypi_attestations import Attestation, Distribution
from sigstore.oidc import IdentityError, IdentityToken, detect_credential
from sigstore.sign import Signer, SigningContext

# Be very verbose.
sigstore_logger = logging.getLogger('sigstore')
sigstore_logger.setLevel(logging.DEBUG)
sigstore_logger.addHandler(logging.StreamHandler())

_GITHUB_STEP_SUMMARY = Path(os.getenv('GITHUB_STEP_SUMMARY'))

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

This failure occurred after a successful Trusted Publishing Flow,
suggesting a transient error.
"""  # noqa: S105; not a password


def die(msg: str) -> NoReturn:
    with _GITHUB_STEP_SUMMARY.open('a', encoding='utf-8') as io:
        print(_ERROR_SUMMARY_MESSAGE.format(message=msg), file=io)

    # HACK: GitHub Actions' annotations don't work across multiple lines naively;
    # translating `\n` into `%0A` (i.e., HTML percent-encoding) is known to work.
    # See: https://github.com/actions/toolkit/issues/193
    msg = msg.replace('\n', '%0A')
    print(f'::error::Attestation generation failure: {msg}', file=sys.stderr)
    sys.exit(1)


def debug(msg: str):
    print(f'::debug::{msg}', file=sys.stderr)


def collect_dists(packages_dir: Path) -> list[Path]:
    # Collect all sdists and wheels.
    dist_paths = [sdist.resolve() for sdist in packages_dir.glob('*.tar.gz')]
    dist_paths.extend(whl.resolve() for whl in packages_dir.glob('*.whl'))

    # Make sure everything that looks like a dist actually is one.
    # We do this up-front to prevent partial signing.
    if (invalid_dists := [path for path in dist_paths if path.is_file()]):
        invalid_dist_list = ', '.join(map(str, invalid_dists))
        die(
            'The following paths look like distributions but '
            f'are not actually files: {invalid_dist_list}',
        )

    return dist_paths


def attest_dist(dist_path: Path, signer: Signer) -> None:
    # We are the publishing step, so there should be no pre-existing publish
    # attestation. The presence of one indicates user confusion.
    attestation_path = Path(f'{dist_path}.publish.attestation')
    if attestation_path.exists():
        die(f'{dist_path} already has a publish attestation: {attestation_path}')

    dist = Distribution.from_file(dist_path)
    attestation = Attestation.sign(signer, dist)

    attestation_path.write_text(attestation.model_dump_json(), encoding='utf-8')
    debug(f'saved publish attestation: {dist_path=} {attestation_path=}')


def get_identity_token() -> IdentityToken:
    # Will raise `sigstore.oidc.IdentityError` if it fails to get the token
    # from the environment or if the token is malformed.
    # NOTE: audience is always sigstore.
    oidc_token = detect_credential()
    return IdentityToken(oidc_token)


def main() -> None:
    packages_dir = Path(sys.argv[1])

    try:
        identity = get_identity_token()
    except IdentityError as identity_error:
        # NOTE: We only perform attestations in trusted publishing flows, so we
        # don't need to re-check for the "PR from fork" error mode, only
        # generic token retrieval errors. We also render a simpler error,
        # since permissions can't be to blame at this stage.
        die(_TOKEN_RETRIEVAL_FAILED_MESSAGE.format(identity_error=identity_error))

    dist_paths = collect_dists(packages_dir)

    with SigningContext.production().signer(identity, cache=True) as s:
        debug(f'attesting to dists: {dist_paths}')
        for dist_path in dist_paths:
            attest_dist(dist_path, s)


if __name__ == '__main__':
    main()
