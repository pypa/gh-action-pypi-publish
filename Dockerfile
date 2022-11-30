FROM python:3.9-slim

LABEL "maintainer" "Sviatoslav Sydorenko <wk+pypa@sydorenko.org.ua>"
LABEL "repository" "https://github.com/pypa/gh-action-pypi-publish"
LABEL "homepage" "https://github.com/pypa/gh-action-pypi-publish"

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

COPY requirements requirements
RUN \
  PIP_CONSTRAINT=requirements/runtime-prerequisites.txt \
    pip install --upgrade --no-cache-dir \
      -r requirements/runtime-prerequisites.in && \
  PIP_CONSTRAINT=requirements/runtime.txt \
    pip install --upgrade --no-cache-dir --prefer-binary \
      -r requirements/runtime.in

WORKDIR /app
COPY LICENSE.md .
COPY twine-upload.sh .
COPY print-hash.py .

RUN chmod +x twine-upload.sh
ENTRYPOINT ["/app/twine-upload.sh"]
