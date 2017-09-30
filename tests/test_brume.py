import unittest

import delegator


class TestTemplate(unittest.TestCase):
    """Test for brume CLI."""

    def test_config(self):
        c = delegator.run('brume config')
        assert c.err == ''
