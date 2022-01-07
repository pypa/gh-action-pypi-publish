#! /usr/bin/env bash
set -Eeuo pipefail


if [[
    "$INPUT_USER" == "__token__" &&
    ! "$INPUT_PASSWORD" =~ ^pypi-
  ]]
then
    echo \
        ::warning file='# >>' PyPA publish to PyPI GHA'%3A' \
        POTENTIALLY INVALID TOKEN \
        '<< ':: \
        It looks like you are trying to use an API token to \
        authenticate in the package index and your token value does \
        not start with '"pypi-"' as it typically should. This may \
        cause an authentication error. Please verify that you have \
        copied your token properly if such an error occurs.
fi

if ( ! ls -A ${INPUT_PACKAGES_DIR%%/}/*.tar.gz &> /dev/null && \
     ! ls -A ${INPUT_PACKAGES_DIR%%/}/*.whl &> /dev/null )
then
    echo \
        ::warning file='# >>' PyPA publish to PyPI GHA'%3A' \
        MISSING DISTS \
        '<< ':: \
        It looks like there are no Python distribution packages to \
        publish in the directory "'${INPUT_PACKAGES_DIR%%/}/'". \
        Please verify that they are in place should you face this \
        problem.
fi

if [[ ${INPUT_VERIFY_METADATA,,} != "false" ]] ; then
    twine check ${INPUT_PACKAGES_DIR%%/}/*
fi

TWINE_EXTRA_ARGS=
if [[ ${INPUT_SKIP_EXISTING,,} != "false" ]] ; then
    TWINE_EXTRA_ARGS=--skip-existing
fi

if [[ ${INPUT_VERBOSE,,} != "false" ]] ; then
    TWINE_EXTRA_ARGS="--verbose $TWINE_EXTRA_ARGS"
fi

TWINE_USERNAME="$INPUT_USER" \
TWINE_PASSWORD="$INPUT_PASSWORD" \
TWINE_REPOSITORY_URL="$INPUT_REPOSITORY_URL" \
  exec twine upload ${TWINE_EXTRA_ARGS} ${INPUT_PACKAGES_DIR%%/}/*

if [[ ${INPUT_PRINT_HASH,,} != "false" ]] ; then
    cat > ./print_hash.py << EOF
import os
import hashlib
sha256 = hashlib.sha256()
md5 = hashlib.md5()
blake2_256 = hashlib.blake2b(digest_size=256 // 8)
file_list = os.listdir(os.path.abspath("${INPUT_PACKAGES_DIR%%/}"))
for i in file_list:
    print(i)
    print("")
    file = open(os.path.abspath(os.path.join("${INPUT_PACKAGES_DIR%%/}", i)), "rb")
    content = file.read()
    file.close()
    sha256.update(content)
    md5.update(content)
    blake2_256.update(content)
    print(f"SHA256: {sha256.hexdigest()}")
    print(f"MD5: {md5.hexdigest()}")
    print(f"BLAKE2-256: {blake2_256.hexdigest()}")
    print("")
EOF
    python ./print_hash.py
    rm ./print_hash.py
fi