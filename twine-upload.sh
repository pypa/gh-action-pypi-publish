#! /usr/bin/env bash
set -Eeuo pipefail


if [[
    "$INPUT_USER" == "__token__" &&
    ! "$INPUT_PASSWORD" =~ ^pypi-
  ]]
then
    >&2 echo \
        [WARNING]: \
        It looks like you are trying to use an API token to \
        authenticate in the package index and your token value does \
        not start with '"pypi-"' as it typically should. This may \
        cause an authentication error. Please verify that you have \
        copied your token properly if such an error occurs.
fi

if [[
    ! -d dist/ ||
    "`ls -l dist/*.tar.gz dist/*.whl`" == "total 0"
  ]]
then
    >&2 echo \
        [WARNING]: \
        It looks like there are no Python distribution packages to \
        publish in the '"dist/"' directory. Please verify that they \
        are in place should you face this problem.
fi


TWINE_USERNAME="$INPUT_USER" \
TWINE_PASSWORD="$INPUT_PASSWORD" \
TWINE_REPOSITORY_URL="$INPUT_REPOSITORY_URL" \
  exec twine upload dist/*
