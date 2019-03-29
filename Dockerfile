FROM python:3.7-slim

LABEL "maintainer"="Sviatoslav Sydorenko <wk+re-actors@sydorenko.org.ua>"
LABEL "repository"="https://github.com/re-actors/pypi-action"
LABEL "homepage"="https://github.com/re-actors/pypi-action"

LABEL "com.github.actions.name"="pypi-action"
LABEL "com.github.actions.description"="Upload Python distribution packages to PyPI"
LABEL "com.github.actions.icon"="upload-cloud"
LABEL "com.github.actions.color"="yellow"

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

ADD LICENSE.md /LICENSE.md

RUN pip install --upgrade --no-cache-dir twine

ENTRYPOINT ["twine"]
CMD ["upload", "dist/*"]
