import unittest

from brume.config import Config


class TestConfig(unittest.TestCase):
    """Test for brume.Config."""

    def test_load(self):
        """A configuration file can be loaded."""
        conf = Config.load()

        assert conf['region'] == 'eu-west-1'
        assert isinstance(conf['stack'], dict)
        assert isinstance(conf['templates'], dict)


if __name__ == '__main__':
    unittest.main()
