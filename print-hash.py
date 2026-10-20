import hashlib
import pathlib
import sys

packages_dir = pathlib.Path(sys.argv[1]).resolve()

for file_object in packages_dir.iterdir():
    sha256 = hashlib.sha256()
    md5 = hashlib.md5()  # noqa: S324; only use for reference
    blake2_256 = hashlib.blake2b(digest_size=256 // 8)

    content = file_object.read_bytes()

    sha256.update(content)
    md5.update(content)
    blake2_256.update(content)

    print(
        ":".join(
            (
                sha256.hexdigest(),
                md5.hexdigest(),
                blake2_256.hexdigest(),
                file_object.name,
            ),
        ),
        end="\0",
    )
