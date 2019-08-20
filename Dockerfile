FROM python:3.7-slim

LABEL "maintainer"="Sviatoslav Sydorenko <wk+re-actors@sydorenko.org.ua>"
LABEL "repository"="https://github.com/re-actors/gh-action-pypi-publish"
LABEL "homepage"="https://github.com/re-actors/gh-action-pypi-publish"

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN pip install --upgrade --no-cache-dir twine

WORKDIR /app
COPY ./LICENSE.md /app/
COPY ./twine-upload.sh /app/

RUN chmod +x /app/twine-upload.sh
ENTRYPOINT ["/app/twine-upload.sh"]
