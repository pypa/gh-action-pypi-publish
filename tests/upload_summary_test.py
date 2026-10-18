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
        assert '**Package index:** PyPI' in content
        assert '**Distribution files:** 2' in content
        assert 'example-1.0.tar.gz' in content
        assert 'README.md' not in content
        assert 'not independently verified' in content

    def test_redacts_custom_index_credentials(self) -> None:
        with TemporaryDirectory() as temp:
            directory = Path(temp)
            (directory / 'a|<bad>.whl').touch()
            summary = upload_summary.render_summary(
                directory,
                'https://person:secret@internal.example.net/legacy/?token=password',
                'True',
            )
        assert 'Custom package index' in summary
        assert 'may not have been uploaded' in summary
        assert 'a|&lt;bad&gt;.whl' in summary
        assert 'secret' not in summary
        assert 'password' not in summary

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
        assert report.startswith('Earlier step notes\n')
        assert '**Package index:** TestPyPI' in report
        assert '<code>one-1.0.whl</code>' in report


if __name__ == '__main__':
    unittest.main()
