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

    def list_sets(self):
        sets_vfs = collections.OrderedDict()
        for (name, set_id, tracks) in self.backend.remote.get_sets():
            sets_list = new_folder(name, ['sets', set_id])
            logger.debug('Adding set %s to vfs' % sets_list.name)
            sets_vfs[set_id] = sets_list
        return sets_vfs.values()

    def list_liked(self):
        vfs_list = collections.OrderedDict()
        for data in self.backend.remote.get_user_liked():
            try:
                name, set_id = data
            except (TypeError, ValueError):
                logger.debug('Adding liked track %s to vfs' % data.name)
                vfs_list[data.name] = models.Ref.track(
                    uri=data.uri, name=data.name
                )
            else:
                logger.debug('Adding liked playlist %s to vfs' % name)
                vfs_list[set_id] = new_folder(name, ['sets', set_id])
        return vfs_list.values()

    def list_user_follows(self):
        sets_vfs = collections.OrderedDict()
        for (name, user_id) in self.backend.remote.get_followings():
            sets_list = new_folder(name, ['following', user_id])
            logger.debug('Adding set %s to vfs' % sets_list.name)
            sets_vfs[user_id] = sets_list
        return sets_vfs.values()

    def list_explore(self):
        sets_vfs = collections.OrderedDict()
        for eid, name in enumerate(self.backend.remote.get_explore()):
            sets_list = new_folder(
                name,
                ['explore', str(eid)]
            )
            logger.debug('Adding explore category %s to vfs' % sets_list.name)
            sets_vfs[str(eid)] = sets_list
        return sets_vfs.values()

    def list_groups(self):
        groups_vfs = collections.OrderedDict()
        for group in self.backend.remote.get_groups():
            g_list = new_folder(
                group.get('name'),
                ['groups', str(group.get('id'))]
            )
            logger.debug('Adding group %s to vfs' % g_list.name)
            groups_vfs[str(group.get('id'))] = g_list
        return groups_vfs.values()

    def tracklist_to_vfs(self, track_list):
        vfs_list = collections.OrderedDict()
        for temp_track in track_list:
            if not isinstance(temp_track, Track):
                temp_track = self.backend.remote.parse_track(temp_track)
            if hasattr(temp_track, 'uri'):
                vfs_list[temp_track.name] = models.Ref.track(
                    uri=temp_track.uri,
                    name=temp_track.name
                )
        return vfs_list.values()

    def browse(self, uri):
        logger.debug('Browse', uri)
        if not self.vfs.get(uri):
            (req_type, res_id) = re.match(r'.*:(\w*)(?:/(\d*))?', uri).groups()
            # Sets
            if 'feed' == req_type:
                return self.list_feed();

            if 'sets' == req_type:
                if res_id:
                    return self.tracklist_to_vfs(
                        self.backend.remote.get_set(res_id)
                    )
                else:
                    return self.list_sets()
            # Following
            if 'following' == req_type:
                if res_id:
                    return self.tracklist_to_vfs(
                        self.backend.remote.get_followings(res_id)
                    )
                else:
                    return self.list_user_follows()
            # Explore
            if 'explore' == req_type:
                if res_id:
                    return self.tracklist_to_vfs(
                        self.backend.remote.get_explore(res_id)
                    )
                else:
                    return self.list_explore()
            # Groups
            if 'groups' == req_type:
                if res_id:
                    return self.tracklist_to_vfs(
                        self.backend.remote.get_groups(res_id)
                    )
                else:
                    return self.list_groups()
            # Liked
            if 'liked' == req_type:
                return self.list_liked()
            # User stream
            if 'stream' == req_type:
                return self.tracklist_to_vfs(
                    self.backend.remote.get_user_stream()
                )

        # root directory
        return self.vfs.get(uri, {}).values()

    def search(self, query=None, uris=None, exact=False):
        # TODO Support exact search

        if not query:
            return

        if 'uri' in query:
            search_query = ''.join(query['uri'])
            url = urlparse(search_query)
            if 'mixcloud.com' in url.netloc:
                logger.info('Resolving Mixcloud for: %s', search_query)
                return SearchResult(
                    uri='mixcloud:search',
                    tracks=self.backend.remote.resolve_url(search_query)
                )
        else:
            search_query = simplify_search_query(query)
            logger.info('Searching Mixcloud for: %s', search_query)
            return SearchResult(
                uri='mixcloud:search',
                tracks=self.backend.remote.search(search_query)
            )

    def lookup(self, uri):
        if 'sc:' in uri:
            uri = uri.replace('sc:', '')
            return self.backend.remote.resolve_url(uri)

        try:
            track_id = self.backend.remote.parse_track_uri(uri)
            track = self.backend.remote.get_track(track_id)
            if track is None:
                logger.info(
                    'Failed to lookup %s: Mixcloud track not found' % uri)
                return []
            return [track]
        except Exception as error:
            logger.error('Failed to lookup %s: %s', uri, error)
            return []