from __future__ import unicode_literals

import collections
import logging
import re
import string
import time
import unicodedata
from multiprocessing.pool import ThreadPool
from urllib import quote_plus

from mopidy.models import Album, Artist, Track

import requests


logger = logging.getLogger(__name__)


def safe_url(uri):
    return quote_plus(
        unicodedata.normalize('NFKD', unicode(uri)).encode('ASCII', 'ignore'))


def readable_url(uri):
    valid_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)
    safe_uri = unicodedata.normalize('NFKD', unicode(uri)).encode('ASCII', 'ignore')
    return re.sub('\s+', ' ',
                  ''.join(c for c in safe_uri if c in valid_chars)).strip()


class cache(object):
    # TODO: merge this to util library

    def __init__(self, ctl=8, ttl=3600):
        self.cache = {}
        self.ctl = ctl
        self.ttl = ttl
        self._call_count = 1

    def __call__(self, func):
        def _memoized(*args):
            self.func = func
            now = time.time()
            try:
                value, last_update = self.cache[args]
                age = now - last_update
                if self._call_count >= self.ctl or age > self.ttl:
                    self._call_count = 1
                    raise AttributeError

                self._call_count += 1
                return value

            except (KeyError, AttributeError):
                value = self.func(*args)
                self.cache[args] = (value, now)
                return value

            except TypeError:
                return self.func(*args)

        return _memoized

def add_cloudcast(index, json):
    if STR_NAME not in json or not json[STR_NAME]:
        logger.warn('name not found in track %s', index)
        return {}
    json_name=json[STR_NAME]
    logger.debug('parsing track %s', json_name)
    json_key=''
    json_year=0
    json_date=''
    json_length=0
    json_userkey=''
    json_username=''
    json_image=''
    json_comment=''
    json_genre=''
    if STR_KEY in json and json[STR_KEY]:
        json_key=json[STR_KEY]
        logger.debug('Key is %s', json_key)
    if STR_CREATEDTIME in json and json[STR_CREATEDTIME]:
        json_created=json[STR_CREATEDTIME]
        json_structtime=time.strptime(json_created[0:10],'%Y-%m-%d')
        json_year=int(time.strftime('%Y',json_structtime))
        json_date=time.strftime('%d/%m/Y',json_structtime)
    if STR_AUDIOLENGTH in json and json[STR_AUDIOLENGTH]:
        json_length=json[STR_AUDIOLENGTH]
    if STR_USER in json and json[STR_USER]:
        json_user=json[STR_USER]
        if STR_KEY in json_user and json_user[STR_KEY]:
            json_userkey=json_user[STR_KEY]
        if STR_NAME in json_user and json_user[STR_NAME]:
            json_username=json_user[STR_NAME]
    if STR_PICTURES in json and json[STR_PICTURES]:
        json_pictures=json[STR_PICTURES]
        if thumb_size in json_pictures and json_pictures[thumb_size]:
            json_image=json_pictures[thumb_size]
    if STR_DESCRIPTION in json and json[STR_DESCRIPTION]:
        json_comment=json[STR_DESCRIPTION].encode('ascii', 'ignore')
    if STR_TAGS in json and json[STR_TAGS]:
        json_tags=json[STR_TAGS]
        for json_tag in json_tags:
            if STR_NAME in json_tag and json_tag[STR_NAME]:
                if json_genre<>'':
                    json_genre += ', '
                json_genre=json_genre+json_tag[STR_NAME]
    infolabels = {
        STR_COUNT:index,
        STR_TRACKNUMBER:index,
        STR_TITLE:json_name,
        STR_ARTIST:json_username,
        STR_DURATION:json_length,
        STR_YEAR:json_year,
        STR_DATE:json_date,
        STR_COMMENT:json_comment,
        STR_GENRE:json_genre,
        STR_KEY:json_key
    }

    return infolabels


STR_ACCESS_TOKEN=u'access_token'
STR_ARTIST=      u'artist'
STR_AUDIOFORMATS=u'audio_formats'
STR_AUDIOLENGTH= u'audio_length'
STR_CLIENTID=    u'Vef7HWkSjCzEFvdhet'
STR_CLIENTSECRET=u'VK7hwemnZWBexDbnVZqXLapVbPK3FFYT'
STR_CLOUDCAST=   u'cloudcast'
STR_COUNT=       u'count'
STR_COMMENT=     u'comment'
STR_CREATEDTIME= u'created_time'
STR_DATA=        u'data'
STR_DATE=        u'date'
STR_DESCRIPTION= u'description'
STR_DURATION=    u'duration'
STR_GENRE=       u'genre'
STR_HISTORY=     u'history'
STR_ID=          u'id'
STR_IMAGE=       u'image'
STR_FORMAT=      u'format'
STR_KEY=         u'key'
STR_LIMIT=       u'limit'
STR_MESSAGE=     u'message'
STR_MODE=        u'mode'
STR_MP3=         u'mp3'
STR_NAME=        u'name'
STR_OFFSET=      u'offset'
STR_PAGELIMIT=   u'page_limit'
STR_PICTURES=    u'pictures'
STR_Q=           u'q'
STR_QUERY=       u'query'
STR_RESULT=      u'result'
STR_STREAMURL=   u'stream_url'
STR_SUCCESS=     u'success'
STR_TAG=         u'tag'
STR_TAGS=        u'tags'
STR_THUMBNAIL=   u'thumbnail'
STR_TITLE=       u'title'
STR_TRACK=       u'track'
STR_TRACKNUMBER= u'tracknumber'
STR_TYPE=        u'type'
STR_USER=        u'user'
STR_YEAR=        u'year'
STR_REDIRECTURI= u'http://forum.kodi.tv/showthread.php?tid=116386'

STR_THUMB_SIZES= {0:u'small',1:u'thumbnail',2:u'medium',3:u'large',4:u'extra_large'}

URL_PLUGIN=         'plugin://music/MixCloud/'
URL_MIXCLOUD=       'http://www.mixcloud.com/'
URL_API=            'http://api.mixcloud.com/'
URL_CATEGORIES=     'http://api.mixcloud.com/categories/'
URL_HOT=            'http://api.mixcloud.com/popular/hot/'
URL_SEARCH=         'http://api.mixcloud.com/search/'
URL_FEED=           'https://api.mixcloud.com/davidarkemp/feed/'
URL_FAVORITES=      'https://api.mixcloud.com/me/favorites/'
URL_FOLLOWINGS=     'https://api.mixcloud.com/me/following/'
URL_FOLLOWERS=      'https://api.mixcloud.com/me/followers/'
URL_LISTENS=        'https://api.mixcloud.com/me/listens/'
URL_UPLOADS=        'https://api.mixcloud.com/me/cloudcasts/'
URL_LISTENLATER=    'https://api.mixcloud.com/me/listen-later/'
URL_PLAYLISTS=      'https://api.mixcloud.com/me/playlists/'
URL_JACKYNIX=       'http://api.mixcloud.com/jackyNIX/'
URL_STREAM=         'http://www.mixcloud.com/api/1/cloudcast/{0}.json?embed_type=cloudcast'
URL_FAVORITE=       'https://api.mixcloud.com{0}favorite/'
URL_FOLLOW=         'https://api.mixcloud.com{0}/follow/'
URL_ADDLISTENLATER= 'https://api.mixcloud.com{0}listen-later/'
URL_TOKEN=          'https://www.mixcloud.com/oauth/access_token'

ext_info = False
thumb_size = STR_THUMB_SIZES[0]

def get_cloudcast(url,parameters,index=1,total=0,forinfo=False):
    logger.debug('Get cloudcast '+url)
    try:
        h=requests.get(url, params=parameters)
        logger.debug('Get cloudcast '+h.url)
        json_cloudcast=h.json()
        return add_cloudcast(index, json_cloudcast)
    except Exception as e:
        logger.error('Get cloudcast failed error=%s' % e)
    return {}


def get_cloudcasts(url,parameters={}):
    found=0

    logger.debug('Get cloudcasts '+url)
    h=requests.get(url, params=parameters)
    logger.debug('Get cloudcasts '+h.url)
    json_content=h.json()
    if STR_DATA in json_content and json_content[STR_DATA] :
        json_data=json_content[STR_DATA]
        total=len(json_data)+1
        json_tracknumber=0
        if STR_OFFSET in parameters:
            json_tracknumber=parameters[STR_OFFSET]
        else:
            json_tracknumber=0

        for json_cloudcast in json_data:
            json_tracknumber=json_tracknumber+1
            if ext_info:
                infolabels = get_cloudcast(URL_API[:-1]+json_cloudcast[STR_KEY],{},json_tracknumber,total)
            else:
                infolabels = add_cloudcast(json_tracknumber, json_cloudcast)
            if len(infolabels)>0:
                found=found+1
    return found

class MixcloudClient(object):

    def __init__(self, config):
        super(MixcloudClient, self).__init__()
        #token = config['auth_token']
        #self.explore_songs = config.get('explore_songs', 10)
        self.http_client = requests.Session()
        #self.http_client.headers.update({'Authorization': 'OAuth %s' % token})

        #try:
        #    self._get('me.json')
        #except Exception as err:
        #    if err.response is not None and err.response.status_code == 401:
        #        logger.error('Invalid "auth_token" used for Mixcloud authentication!')
        #    else:
        #        raise

    @property
    @cache()
    def user(self):
        return self._get('me.json')

    #@cache()
    def get_user_stream(self):
        logger.debug("Get user stream")
        result = self.http_client.get(URL_FEED).json()
        logger.debug(result[u'data'][0].keys())
        return self.sanitize_tracks([add_cloudcast(0, track) for track in result[u'data'][0]['cloudcasts']])

    @cache()
    def get_explore_categories(self):
        return self._get('explore/categories', 'api-v2').get('music')

    def get_explore(self, query_explore_id=None):
        explore = self.get_explore_categories()
        if query_explore_id:
            url = 'explore/{urn}?limit={limit}&offset=0&linked_partitioning=1'\
                .format(
                    urn=explore[int(query_explore_id)],
                    limit=self.explore_songs
                )
            web_tracks = self._get(url, 'api-v2')
            track_ids = map(lambda x: x.get('id'), web_tracks.get('tracks'))
            return self.resolve_tracks(track_ids)
        return explore

    def get_groups(self, query_group_id=None):

        if query_group_id:
            web_tracks = self._get(
                'groups/%d/tracks.json' % int(query_group_id))
            tracks = []
            for track in web_tracks:
                if 'track' in track.get('kind'):
                    tracks.append(self.parse_track(track))
            return self.sanitize_tracks(tracks)
        else:
            return self._get('me/groups.json')

    def get_followings(self, query_user_id=None):

        if query_user_id:
            return self._get('users/%s/tracks.json' % query_user_id)

        users = []
        for playlist in self._get('me/followings.json?limit=60'):
            name = playlist.get('username')
            user_id = str(playlist.get('id'))
            logger.debug('Fetched user %s with id %s' % (
                name, user_id
            ))

            users.append((name, user_id))
        return users

    @cache()
    def get_set(self, set_id):
        playlist = self._get('playlists/%s.json' % set_id)
        return playlist.get('tracks', [])

    def get_sets(self):
        playable_sets = []
        for playlist in self._get('me/playlists.json?limit=1000'):
            name = playlist.get('title')
            set_id = str(playlist.get('id'))
            tracks = playlist.get('tracks')
            logger.debug('Fetched set %s with id %s (%d tracks)' % (
                name, set_id, len(tracks)
            ))
            playable_sets.append((name, set_id, tracks))
        return playable_sets

    def get_user_liked(self):
        # Note: As with get_user_stream, this API call is undocumented.
        likes = []
        liked = self._get('e1/me/likes.json?limit=1000')
        for data in liked:

            track = data['track']
            if track:
                likes.append(self.parse_track(track))

            pl = data['playlist']
            if pl:
                likes.append((pl['title'], str(pl['id'])))

        return self.sanitize_tracks(likes)

    # Public
    @cache()
    def get_track(self, track_id, streamable=False):
        logger.debug('Getting info for track with id %s' % track_id)
        try:
            return self.parse_track(self._get('tracks/%s.json' % track_id),
                                    streamable)
        except Exception:
            return None

    def parse_track_uri(self, track):
        logger.debug('Parsing track %s' % (track))
        if hasattr(track, "uri"):
            track = track.uri
        return track.split('.')[-1]

    def search(self, query):

        search_results = self._get(
            'tracks.json?q=%s&filter=streamable&order=hotness&limit=%d' % (
                quote_plus(query.encode('utf-8')), self.explore_songs))
        tracks = []
        for track in search_results:
            tracks.append(self.parse_track(track, False))
        return self.sanitize_tracks(tracks)

    def parse_results(self, res):
        tracks = []
        for track in res:
            tracks.append(self.parse_track(track))
        return self.sanitize_tracks(tracks)

    def resolve_url(self, uri):
        return self.parse_results([self._get('resolve.json?url=%s' % uri)])

    def _get(self, url, endpoint='api'):
        if '?' in url:
            url = '%s&client_id=%s' % (url, self.CLIENT_ID)
        else:
            url = '%s?client_id=%s' % (url, self.CLIENT_ID)

        url = 'https://%s.mixcloud.com/%s' % (endpoint, url)

        logger.debug('Requesting %s' % url)
        res = self.http_client.get(url)
        res.raise_for_status()
        return res.json()

    def sanitize_tracks(self, tracks):
        return filter(None, tracks)

    @cache()
    def parse_track(self, data, remote_url=False):
        if not data:
            return None

        # NOTE kwargs dict keys must be bytestrings to work on Python < 2.6.5
        # See https://github.com/mopidy/mopidy/issues/302 for details.

        track_kwargs = {}
        artist_kwargs = {}
        album_kwargs = {}

        if STR_NAME in data:
            name = data[STR_NAME]
            label_name = data.get(STR_NAME)

            if bool(label_name):
                track_kwargs[b'name'] = name
                artist_kwargs[b'name'] = label_name
            else:
                track_kwargs[b'name'] = name
                artist_kwargs[b'name'] = data.get(STR_USER)

            album_kwargs[b'name'] = 'Mixcloud'

        if STR_DATE in data:
            track_kwargs[b'date'] = data[STR_DATE]

        if remote_url:
            track_kwargs[b'uri'] = self.get_streamble_url(data['stream_url'])
        else:
            track_kwargs[b'uri'] = 'mixcloud:song/%s.%s' % (
                readable_url(data.get('title')), data.get('id')
            )

        track_kwargs[b'length'] = int(data.get('duration', 0))
        track_kwargs[b'comment'] = data.get('permalink_url', '')

        if artist_kwargs:
            artist = Artist(**artist_kwargs)
            track_kwargs[b'artists'] = [artist]

        if album_kwargs:
            if 'artwork_url' in data and data['artwork_url']:
                album_kwargs[b'images'] = [data['artwork_url']]
            else:
                image = data.get('user').get('avatar_url')
                album_kwargs[b'images'] = [image]

            album = Album(**album_kwargs)
            track_kwargs[b'album'] = album

        track = Track(**track_kwargs)
        return track

    @cache()
    def can_be_streamed(self, url):
        req = self.http_client.head(self.get_streamble_url(url))
        return req.status_code == 302

    def get_streamble_url(self, url):
        return '%s?client_id=%s' % (url, self.CLIENT_ID)

    def resolve_tracks(self, track_ids):
        """Resolve tracks concurrently emulating browser

        :param track_ids:list of track ids
        :return:list `Track`
        """
        pool = ThreadPool(processes=16)
        tracks = pool.map(self.get_track, track_ids)
        pool.close()
        return self.sanitize_tracks(tracks)
