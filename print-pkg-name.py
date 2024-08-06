import pathlib
import sys

from packaging import utils


def debug(msg: str):
    print(f'::debug::{msg.title()}', file=sys.stderr)


packages_dir = pathlib.Path(sys.argv[1]).resolve().absolute()

wheel_file_names = [
    f.name for f in packages_dir.iterdir() if f.suffix == '.whl'
]
sdist_file_names = [
    f.name for f in packages_dir.iterdir() if f.suffix == '.gz'
]

# Parse the package name from the distribution files and print it. On error,
# don't print anything.
if wheel_file_names:
    try:
        print(utils.parse_wheel_filename(wheel_file_names[0])[0])
    except utils.InvalidWheelFilename:
        debug(f'Invalid wheel filename: {wheel_file_names[0]}')
elif sdist_file_names:
    try:
        print(utils.parse_sdist_filename(sdist_file_names[0])[0])
    except utils.InvalidSdistFilename:
        debug(f'Invalid sdist filename: {sdist_file_names[0]}')
