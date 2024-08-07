import pathlib
import sys

from packaging import utils


def debug(msg: str):
    print(f'::debug::{msg.title()}', file=sys.stderr)


def safe_parse_pkg_name(file_path: pathlib.Path) -> str | None:
    if file_path.suffix == '.whl':
        try:
            return utils.parse_wheel_filename(file_path.name)[0]
        except utils.InvalidWheelFilename:
            debug(f'Invalid wheel filename: {file_path.name}')
            return None
    elif file_path.suffix == '.gz':
        try:
            return utils.parse_sdist_filename(file_path.name)[0]
        except utils.InvalidSdistFilename:
            debug(f'Invalid sdist filename: {file_path.name}')
            return None
    return None


packages_dir = pathlib.Path(sys.argv[1]).resolve()

pkg_names = {safe_parse_pkg_name(f) for f in packages_dir.iterdir()}
pkg_names.discard(None)

for p in pkg_names:
    print(p)
