FROM python:3.7-slim

LABEL "maintainer"="Sviatoslav Sydorenko <wk+re-actors@sydorenko.org.ua>"
LABEL "repository"="https://github.com/re-actors/gh-action-pypi-publish"
LABEL "homepage"="https://github.com/re-actors/gh-action-pypi-publish"

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

ADD LICENSE.md /LICENSE.md

RUN pip install --upgrade --no-cache-dir twine

ENTRYPOINT ["twine"]
CMD ["upload", "dist/*"]
