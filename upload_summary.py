"""Summarize completed Twine invocations without exposing publishing credentials."""

from __future__ import annotations

import html
import os
from pathlib import Path


def _index_label(repository_url: str) -> str:
    # Only identify trusted public indices: never print private hosts or tokens.
    if repository_url == 'https://upload.pypi.org/legacy/':
        return 'PyPI'
    if repository_url == 'https://test.pypi.org/legacy/':
        return 'TestPyPI'
    return 'Custom package index'


def _display_name(filename: str) -> str:
    # Filename is controlled by workflow inputs. Escape markup and newlines.
    safe = filename.replace('\r', '?').replace('\n', '?')
    return html.escape(safe[:200], quote=True)


def render_summary(packages_dir: Path, repository_url: str, skip_existing: str) -> str:
    names = sorted(
        p.name for p in packages_dir.iterdir()
        if p.is_file() and p.name.endswith(('.whl', '.tar.gz', '.zip'))
    )
    lines = [
        '## Python package publication', '',
        f'**Package index:** {_index_label(repository_url)}', '',
        'Twine finished without an error. These files were supplied to the '
        'publishing step, not independently verified on the remote index.', '',
    ]
    if skip_existing.lower() == 'false':
        lines.append('**Skip existing:** Disabled.')
    else:
        lines.append(
            '**Skip existing:** Enabled. Files already on the index '
            'may not have been uploaded.',
        )
    lines.extend(['', f'**Distribution files:** {len(names)}', ''])
    for filename in names[:50]:
        lines.append(f'- <code>{_display_name(filename)}</code>')
    if len(names) > 50:
        extra_count = len(names) - 50
        lines.append(f'- … and {extra_count} more files')
    return '\n'.join([*lines, ''])


def main() -> None:
    summary_file = os.environ.get('GITHUB_STEP_SUMMARY')
    if not summary_file:
        return
    text = render_summary(
        Path(os.environ['PYPI_SUMMARY_PACKAGES_DIR']),
        os.environ['PYPI_SUMMARY_REPOSITORY_URL'],
        os.environ['PYPI_SUMMARY_SKIP_EXISTING'],
    )
    with open(summary_file, 'a', encoding='utf-8') as output:
        output.write(text)


if __name__ == '__main__':
    main()
