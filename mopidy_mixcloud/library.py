from __future__ import unicode_literals

import collections
import logging
import re
import urllib
from urlparse import urlparse

from mopidy import backend, models
from mopidy.models import SearchResult, Track

from mopidy_mixcloud.mixcloud import safe_url


logger = logging.getLogger(__name__)


def generate_uri(path):
    return 'mixcloud:directory:%s' % urllib.quote('/'.join(path))


def new_folder(name, path):
    return models.Ref.directory(
        uri=generate_uri(path),
        name=safe_url(name)
    )


def simplify_search_query(query):

    if isinstance(query, dict):
        r = []
        for v in query.values():
            if isinstance(v, list):
                r.extend(v)
            else:
                r.append(v)
        return ' '.join(r)
    if isinstance(query, list):
        return ' '.join(query)
    else:
        return query


class MixcloudLibraryProvider(backend.LibraryProvider):
    root_directory = models.Ref.directory(
        uri='mixcloud:directory',
        name='Mixcloud'
    )

    def __init__(self, *args, **kwargs):
        super(MixcloudLibraryProvider, self).__init__(*args, **kwargs)
        self.vfs = {'mixcloud:directory': collections.OrderedDict()}
        self.add_to_vfs(new_folder('Feed', ['feed']))


    def add_to_vfs(self, _model):
        self.vfs['mixcloud:directory'][_model.uri] = _model

    def list_feed(self):
        logger.debug('loading feed')
        feed = []
        for cast in self.backend.remote.get_user_stream():
            logger.debug('found feed track', cast.get(u'key'))
            feed.append(models.Ref.track(uri="mixcloud:"+cast.get(u'key'), name=cast.get(u'title')))
        return feed



    def browse(self, uri):
        logger.debug('Browse', uri)
        if not self.vfs.get(uri):
            (req_type, res_id) = re.match(r'.*:(\w*)(?:/(\d*))?', uri).groups()
            # Sets
            if 'feed' == req_type:
                return self.list_feed()

        # root directory
        return self.vfs.get(uri, {}).values()

    def lookup(self, uri):
        if 'mixcloud:' in uri:


            uri = uri.replace('mixcloud:', '')
            return [self.backend.remote.resolve_url(uri)]

        return []
