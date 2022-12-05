import hashlib
import pathlib
import sys

packages_dir = pathlib.Path(sys.argv[1]).resolve().absolute()

print("Showing hash values of files to be uploaded:")

for file_object in packages_dir.iterdir():
    sha256 = hashlib.sha256()
    md5 = hashlib.md5()
    blake2_256 = hashlib.blake2b(digest_size=256 // 8)

    print(file_object)
    print("")

    content = file_object.read_bytes()

    sha256.update(content)
    md5.update(content)
    blake2_256.update(content)

    print(f"SHA256: {sha256.hexdigest()}")
    print(f"MD5: {md5.hexdigest()}")
    print(f"BLAKE2-256: {blake2_256.hexdigest()}")
    print("")
