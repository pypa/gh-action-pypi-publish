import sys

from packaging.version import parse

print(sys.version_info)
tag_ref = sys.argv[1]
tag_name = tag_ref.split("/")[-1]
print(f"tag_name: {tag_name}")
version = parse(tag_name)
print(f"version: {version}")
if not (version.is_prerelease):
    print("Creating new major and minor tags!")
    print(f"::set-output name=original_tag_name::{tag_name}")
    print(f"::set-output name=major_version::v{version.major}")
    print(f"::set-output name=minor_version::v{version.major}.{version.minor}")
else:
    print("No tags created (dev or pre version)!")
