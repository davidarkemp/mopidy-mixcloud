from __future__ import unicode_literals

import logging

from mopidy import backend

import pykka

from .library import MixcloudLibraryProvider
from .mixcloud import MixcloudClient


logger = logging.getLogger(__name__)


class MixcloudBackend(pykka.ThreadingActor, backend.Backend):

    def __init__(self, config, audio):
        super(MixcloudBackend, self).__init__()
        logger.debug("Mixcloud Backend starting")
        self.config = config
        self.remote = MixcloudClient(config['mixcloud'])
        self.library = MixcloudLibraryProvider(backend=self)
        self.playback = MixcloudPlaybackProvider(audio=audio, backend=self)

        self.uri_schemes = ['mixcloud', 'mc']


class MixcloudPlaybackProvider(backend.PlaybackProvider):

    def translate_uri(self, uri):
        logger.debug('translate track from %s' % uri)
        uri = uri.replace('mixcloud:', '')
        return self.backend.remote.get_track_uri(uri)
