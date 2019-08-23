# !/usr/bin/env bash
set -Eeuo pipefail

TWINE_USERNAME=$INPUT_USER \
  TWINE_PASSWORD=$INPUT_PASSWORD \
  TWINE_REPOSITORY_URL=$INPUT_REPOSITORY_URL \
  exec twine upload dist/*
