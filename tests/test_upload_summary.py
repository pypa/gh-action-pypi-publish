from pathlib import Path
from tempfile import TemporaryDirectory
import os
import unittest
from unittest.mock import patch

import upload_summary


class SummaryTests(unittest.TestCase):
    def test_standard_index_and_distributions(self):
        with TemporaryDirectory() as temp:
            directory = Path(temp)
            for name in ('example-1.0-py3-none-any.whl', 'example-1.0.tar.gz', 'README.md'):
                (directory / name).touch()
            content = upload_summary.render_summary(
                directory, 'https://upload.pypi.org/legacy/', 'false'
            )
        self.assertIn('**Package index:** PyPI', content)
        self.assertIn('**Distribution files:** 2', content)
        self.assertIn('example-1.0.tar.gz', content)
        self.assertNotIn('README.md', content)
        self.assertIn('not independently verified', content)

    def test_skip_existing_and_custom_index_hide_secrets(self):
        with TemporaryDirectory() as temp:
            directory = Path(temp)
            (directory / 'a|<bad>.whl').touch()
            summary = upload_summary.render_summary(
                directory,
                'https://person:secret@internal.example.net/legacy/?token=password',
                'True',
            )
        self.assertIn('Custom package index', summary)
        self.assertIn('may not have been uploaded', summary)
        self.assertIn('a|&lt;bad&gt;.whl', summary)
        self.assertNotIn('secret', summary)
        self.assertNotIn('password', summary)

    def test_unset_summary_file_is_noop(self):
        with patch.dict(os.environ, {}, clear=True):
            upload_summary.main()

    def test_summary_append_preserves_prior_content(self):
        with TemporaryDirectory() as temp:
            directory = Path(temp)
            (directory / 'one-1.0.whl').touch()
            summary_file = directory / 'job-summary.md'
            summary_file.write_text('Earlier step notes\n', encoding='utf-8')
            with patch.dict(os.environ, {
                'GITHUB_STEP_SUMMARY': str(summary_file),
                'PYPI_SUMMARY_PACKAGES_DIR': str(directory),
                'PYPI_SUMMARY_REPOSITORY_URL': 'https://test.pypi.org/legacy/',
                'PYPI_SUMMARY_SKIP_EXISTING': 'false',
            }):
                upload_summary.main()
            report = summary_file.read_text(encoding='utf-8')
        self.assertTrue(report.startswith('Earlier step notes\n'))
        self.assertIn('**Package index:** TestPyPI', report)
        self.assertIn('<code>one-1.0.whl</code>', report)


if __name__ == '__main__':
    unittest.main()
