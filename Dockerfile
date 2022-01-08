FROM python:3.9-slim

LABEL "maintainer" "Sviatoslav Sydorenko <wk+pypa@sydorenko.org.ua>"
LABEL "repository" "https://github.com/pypa/gh-action-pypi-publish"
LABEL "homepage" "https://github.com/pypa/gh-action-pypi-publish"

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN \
  pip install --upgrade --no-cache-dir pip-with-requires-python && \
  pip install --upgrade --no-cache-dir --prefer-binary twine

WORKDIR /app
COPY LICENSE.md .
COPY twine-upload.sh .
COPY print-hash.py .

RUN chmod +x twine-upload.sh
ENTRYPOINT ["/app/twine-upload.sh"]
