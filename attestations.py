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


def debug(msg: str) -> None:
    print(f'::debug::{msg}', file=sys.stderr)


def collect_dists(packages_dir: Path) -> list[Path]:
    # Collect all sdists and wheels.
    dist_paths = [sdist.resolve() for sdist in packages_dir.glob('*.tar.gz')]
    dist_paths.extend(sdist.resolve() for sdist in packages_dir.glob('*.zip'))
    dist_paths.extend(whl.resolve() for whl in packages_dir.glob('*.whl'))

    # Make sure everything that looks like a dist actually is one.
    # We do this up-front to prevent partial signing.
    if (invalid_dists := [path for path in dist_paths if not path.is_file()]):
        invalid_dist_list = ', '.join(map(str, invalid_dists))
        die(
            'The following paths look like distributions but '
            f'are not actually files: {invalid_dist_list}',
        )

    return dist_paths


def assert_attestations_do_not_pre_exist(
        dist_to_attestation_map: dict[Path, Path],
) -> None:
    existing_attestations = {
        f'* {dist !s} -> {dist_attestation !s}'
        for dist, dist_attestation in dist_to_attestation_map.items()
        if dist_attestation.exists()
    }
    if not existing_attestations:
        return

    existing_attestations_list = '\n'.join(map(str, existing_attestations))
    error_message = (
        'The following distributions already have publish attestations: '
        f'{existing_attestations_list}'
    )
    die(error_message)


def compose_attestation_mapping(dist_paths: list[Path]) -> dict[Path, Path]:
    dist_to_attestation_map = {
        dist_path: dist_path.with_suffix(
            f'{dist_path.suffix}.publish.attestation',
        )
        for dist_path in dist_paths
    }

    # We are the publishing step, so there should be no pre-existing publish
    # attestation. The presence of one indicates user confusion.
    # Make sure there's no publish attestations on disk.
    # We do this up-front to prevent partial signing.
    assert_attestations_do_not_pre_exist(dist_to_attestation_map)

    return dist_to_attestation_map


def attest_dist(
        dist_path: Path,
        attestation_path: Path,
        signer: Signer,
) -> None:
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
    dist_to_attestation_map = compose_attestation_mapping(
        collect_dists(Path(sys.argv[1])),
    )

    try:
        identity = get_identity_token()
    except IdentityError as identity_error:
        # NOTE: We only perform attestations in trusted publishing flows, so we
        # don't need to re-check for the "PR from fork" error mode, only
        # generic token retrieval errors. We also render a simpler error,
        # since permissions can't be to blame at this stage.
        die(_TOKEN_RETRIEVAL_FAILED_MESSAGE.format(identity_error=identity_error))

    with SigningContext.production().signer(identity, cache=True) as signer:
        debug(f'attesting to dists: {dist_to_attestation_map.keys()}')
        for dist_path, attestation_path in dist_to_attestation_map.items():
            attest_dist(dist_path, attestation_path, signer)


if __name__ == '__main__':
    main()
