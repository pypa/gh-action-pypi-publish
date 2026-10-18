import os
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

import upload_summary


class SummaryTests(unittest.TestCase):
    def test_standard_index_and_distributions(self) -> None:
        with TemporaryDirectory() as temp:
            directory = Path(temp)
            for name in ('example-1.0-py3-none-any.whl', 'example-1.0.tar.gz', 'README.md'):
                (directory / name).touch()
            content = upload_summary.render_summary(
                directory, 'https://upload.pypi.org/legacy/', 'false',
            )
        expected_text = (
            '**Package index:** PyPI',
            '**Distribution files:** 2',
            'example-1.0.tar.gz',
            'not independently verified',
        )
        for expected in expected_text:
            with self.subTest(expected=expected):
                self.assertIn(expected, content)  # noqa: PT009
        self.assertNotIn('README.md', content)  # noqa: PT009

    def test_redacts_custom_index_credentials(self) -> None:
        with TemporaryDirectory() as temp:
            directory = Path(temp)
            (directory / 'a|<bad>.whl').touch()
            summary = upload_summary.render_summary(
                directory,
                'https://person:secret@internal.example.net/legacy/?token=password',
                'True',
            )
        for expected in ('Custom package index', 'may not have been uploaded', 'a|&lt;bad&gt;.whl'):
            with self.subTest(expected=expected):
                self.assertIn(expected, summary)  # noqa: PT009
        for secret in ('secret', 'password'):
            with self.subTest(secret=secret):
                self.assertNotIn(secret, summary)  # noqa: PT009

    def test_unset_summary_file_is_noop(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            upload_summary.main()

    def test_summary_append_preserves_prior_content(self) -> None:
        with TemporaryDirectory() as temp:
            directory = Path(temp)
            (directory / 'one-1.0.whl').touch()
            summary_file = directory / 'job-summary.md'
            summary_file.write_text('Earlier step notes\n', encoding='utf-8')
            with patch.dict(
                os.environ, {
                    'GITHUB_STEP_SUMMARY': str(summary_file),
                    'PYPI_SUMMARY_PACKAGES_DIR': str(directory),
                    'PYPI_SUMMARY_REPOSITORY_URL': 'https://test.pypi.org/legacy/',
                    'PYPI_SUMMARY_SKIP_EXISTING': 'false',
                },
            ):
                upload_summary.main()
            report = summary_file.read_text(encoding='utf-8')
        self.assertTrue(report.startswith('Earlier step notes\n'))  # noqa: PT009
        for expected in ('**Package index:** TestPyPI', '<code>one-1.0.whl</code>'):
            with self.subTest(expected=expected):
                self.assertIn(expected, report)  # noqa: PT009


if __name__ == '__main__':
    unittest.main()
