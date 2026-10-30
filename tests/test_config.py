import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from provider_imagegen.config import load_provider_config


class ProviderCredentialsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def config(self, extra=''):
        (self.root / 'config.toml').write_text(
            'model_provider="custom"\n[model_providers.custom]\n'
            'base_url="https://example.com/v1/"\n' + extra)

    def test_cc_switch_without_auth_file(self):
        self.config('experimental_bearer_token="provider-test"\n')
        result = load_provider_config(self.root)
        self.assertEqual(result.api_key, 'provider-test')
        self.assertEqual(result.base_url, 'https://example.com/v1')

    def test_provider_credentials_win_over_auth(self):
        self.config('experimental_bearer_token="provider-test"\n')
        (self.root / 'auth.json').write_text(json.dumps({'OPENAI_API_KEY': 'legacy-test'}))
        self.assertEqual(load_provider_config(self.root).api_key, 'provider-test')

    def test_environment_key(self):
        self.config('env_key="IMAGE_TEST_KEY"\nexperimental_bearer_token="other-test"\n')
        with patch.dict(os.environ, {'IMAGE_TEST_KEY': 'env-test'}):
            self.assertEqual(load_provider_config(self.root).api_key, 'env-test')
        with patch.dict(os.environ, {'IMAGE_TEST_KEY': ''}):
            with self.assertRaisesRegex(ValueError, 'empty or not set'):
                load_provider_config(self.root)

    def test_legacy_auth(self):
        self.config()
        (self.root / 'auth.json').write_text(json.dumps({'OPENAI_API_KEY': 'legacy-test'}))
        self.assertEqual(load_provider_config(self.root).api_key, 'legacy-test')

    def test_explicit_overrides_without_files(self):
        self.assertEqual(load_provider_config(self.root, 'https://example.com', 'override-test').api_key, 'override-test')

    def test_missing_credentials(self):
        self.config()
        with self.assertRaisesRegex(ValueError, 'API key is missing'):
            load_provider_config(self.root)


if __name__ == '__main__':
    unittest.main()
