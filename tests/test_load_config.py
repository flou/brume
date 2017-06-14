import os
from unittest import TestCase, main
from brume.config import Config


class TestLoadConfig(TestCase):
    def test_load_config(self):
        current_path = os.path.dirname(os.path.abspath(__file__))
        config_template = os.path.join(current_path, 'test_load_config.yml')
        conf = Config.load(config_template)

        assert conf['region'] == 'eu-west-1'
        assert isinstance(conf['stack'], dict)
        assert isinstance(conf['templates'], dict)


if __name__ == '__main__':
    main()
