from __future__ import unicode_literals

import os

from mopidy import config, ext
from mopidy.exceptions import ExtensionError


__version__ = '0.0.1'


class MixcloudExtension(ext.Extension):

    dist_name = 'Mopidy-Mixcloud'
    ext_name = 'mixcloud'
    version = __version__

    def get_default_config(self):
        conf_file = os.path.join(os.path.dirname(__file__), 'ext.conf')
        return config.read(conf_file)

    def get_config_schema(self):
        schema = super(MixcloudExtension, self).get_config_schema()
        #schema['explore_songs'] = config.Integer()
        #schema['auth_token'] = config.Secret()
        return schema

    def validate_config(self, config):  # no_coverage
        if not config.getboolean('mixcloud', 'enabled'):
            return

    def setup(self, registry):
        from .actor import MixcloudBackend
        registry.add('backend', MixcloudBackend)
