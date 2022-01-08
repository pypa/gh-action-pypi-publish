import os
import hashlib

sha256 = hashlib.sha256()
md5 = hashlib.md5()
blake2_256 = hashlib.blake2b(digest_size=256 // 8)

file_list = os.listdir(os.path.abspath(os.getenv("INPUT_PACKAGES_DIR")))

for file in file_list:
    print(file)
    print("")

    with open(os.path.abspath(os.path.join(os.getenv("INPUT_PACKAGES_DIR"), file)), "rb") as f:
        content = f.read()
    
    sha256.update(content)
    md5.update(content)
    blake2_256.update(content)

    print(f"SHA256: {sha256.hexdigest()}")
    print(f"MD5: {md5.hexdigest()}")
    print(f"BLAKE2-256: {blake2_256.hexdigest()}")
    print("")
