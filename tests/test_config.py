import os
import unittest

from brume.config import Config


class TestConfig(unittest.TestCase):
    """Test for brume.Config."""

    def test_load(self):
        """A configuration file can be loaded."""
        current_path = os.path.dirname(os.path.abspath(__file__))
        config_template = os.path.join(current_path, 'test_load_config.yml')
        conf = Config.load(config_template)

        assert conf['region'] == 'eu-west-1'
        assert isinstance(conf['stack'], dict)
        assert isinstance(conf['templates'], dict)


if __name__ == '__main__':
    unittest.main()
