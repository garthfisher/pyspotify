from __future__ import unicode_literals

import mock
import unittest

import spotify
from spotify import utils
import tests


@mock.patch('spotify.artist.lib', spec=spotify.lib)
class ArtistTest(unittest.TestCase):

    def create_session(self, lib_mock):
        session = mock.sentinel.session
        session._sp_session = mock.sentinel.sp_session
        spotify.session_instance = session
        return session

    def tearDown(self):
        spotify.session_instance = None

    def test_create_without_uri_or_sp_artist_fails(self, lib_mock):
        self.assertRaises(AssertionError, spotify.Artist)

    @mock.patch('spotify.Link', spec=spotify.Link)
    def test_create_from_uri(self, link_mock, lib_mock):
        sp_artist = spotify.ffi.new('int *')
        link_instance_mock = link_mock.return_value
        link_instance_mock.as_artist.return_value = spotify.Artist(
            sp_artist=sp_artist)
        lib_mock.sp_link_as_artist.return_value = sp_artist
        uri = 'spotify:artist:foo'

        result = spotify.Artist(uri)

        link_mock.assert_called_with(uri)
        link_instance_mock.as_artist.assert_called_with()
        lib_mock.sp_artist_add_ref.assert_called_with(sp_artist)
        self.assertEqual(result._sp_artist, sp_artist)

    @mock.patch('spotify.Link', spec=spotify.Link)
    def test_create_from_uri_fail_raises_error(self, link_mock, lib_mock):
        link_instance_mock = link_mock.return_value
        link_instance_mock.as_artist.return_value = None
        lib_mock.sp_link_as_artist.return_value = spotify.ffi.NULL
        uri = 'spotify:artist:foo'

        self.assertRaises(ValueError, spotify.Artist, uri)

    def test_adds_ref_to_sp_artist_when_created(self, lib_mock):
        sp_artist = spotify.ffi.new('int *')

        spotify.Artist(sp_artist=sp_artist)

        lib_mock.sp_artist_add_ref.assert_called_with(sp_artist)

    def test_releases_sp_artist_when_artist_dies(self, lib_mock):
        sp_artist = spotify.ffi.new('int *')

        artist = spotify.Artist(sp_artist=sp_artist)
        artist = None  # noqa
        tests.gc_collect()

        lib_mock.sp_artist_release.assert_called_with(sp_artist)

    @mock.patch('spotify.Link', spec=spotify.Link)
    def test_repr(self, link_mock, lib_mock):
        link_instance_mock = link_mock.return_value
        link_instance_mock.uri = 'foo'
        sp_artist = spotify.ffi.new('int *')
        artist = spotify.Artist(sp_artist=sp_artist)

        result = repr(artist)

        self.assertEqual(result, 'Artist(%r)' % 'foo')

    def test_name(self, lib_mock):
        lib_mock.sp_artist_name.return_value = spotify.ffi.new(
            'char[]', b'Foo Bar Baz')
        sp_artist = spotify.ffi.new('int *')
        artist = spotify.Artist(sp_artist=sp_artist)

        result = artist.name

        lib_mock.sp_artist_name.assert_called_once_with(sp_artist)
        self.assertEqual(result, 'Foo Bar Baz')

    def test_name_is_none_if_unloaded(self, lib_mock):
        lib_mock.sp_artist_name.return_value = spotify.ffi.new('char[]', b'')
        sp_artist = spotify.ffi.new('int *')
        artist = spotify.Artist(sp_artist=sp_artist)

        result = artist.name

        lib_mock.sp_artist_name.assert_called_once_with(sp_artist)
        self.assertIsNone(result)

    def test_is_loaded(self, lib_mock):
        lib_mock.sp_artist_is_loaded.return_value = 1
        sp_artist = spotify.ffi.new('int *')
        artist = spotify.Artist(sp_artist=sp_artist)

        result = artist.is_loaded

        lib_mock.sp_artist_is_loaded.assert_called_once_with(sp_artist)
        self.assertTrue(result)

    @mock.patch('spotify.utils.load')
    def test_load(self, load_mock, lib_mock):
        sp_artist = spotify.ffi.new('int *')
        artist = spotify.Artist(sp_artist=sp_artist)

        artist.load(10)

        load_mock.assert_called_with(artist, timeout=10)

    @mock.patch('spotify.image.lib', spec=spotify.lib)
    def test_portrait(self, image_lib_mock, lib_mock):
        session = self.create_session(lib_mock)
        sp_image_id = spotify.ffi.new('char[]', b'portrait-id')
        lib_mock.sp_artist_portrait.return_value = sp_image_id
        sp_image = spotify.ffi.new('int *')
        lib_mock.sp_image_create.return_value = sp_image
        sp_artist = spotify.ffi.new('int *')
        artist = spotify.Artist(sp_artist=sp_artist)
        image_size = spotify.ImageSize.SMALL

        result = artist.portrait(image_size)

        lib_mock.sp_artist_portrait.assert_called_with(
            sp_artist, int(image_size))
        lib_mock.sp_image_create.assert_called_with(
            session._sp_session, sp_image_id)

        self.assertIsInstance(result, spotify.Image)
        self.assertEqual(result._sp_image, sp_image)

        # Since we *created* the sp_image, we already have a refcount of 1 and
        # shouldn't increase the refcount when wrapping this sp_image in an
        # Image object
        self.assertEqual(image_lib_mock.sp_image_add_ref.call_count, 0)

    def test_portrait_is_none_if_null(self, lib_mock):
        lib_mock.sp_artist_portrait.return_value = spotify.ffi.NULL
        sp_artist = spotify.ffi.new('int *')
        artist = spotify.Artist(sp_artist=sp_artist)

        result = artist.portrait()

        lib_mock.sp_artist_portrait.assert_called_with(
            sp_artist, int(spotify.ImageSize.NORMAL))
        self.assertIsNone(result)

    @mock.patch('spotify.Link', spec=spotify.Link)
    def test_portrait_link_creates_link_to_portrait(self, link_mock, lib_mock):
        sp_artist = spotify.ffi.new('int *')
        artist = spotify.Artist(sp_artist=sp_artist)
        sp_link = spotify.ffi.new('int *')
        lib_mock.sp_link_create_from_artist_portrait.return_value = sp_link
        link_mock.return_value = mock.sentinel.link

        result = artist.portrait_link(spotify.ImageSize.NORMAL)

        lib_mock.sp_link_create_from_artist_portrait.assert_called_once_with(
            sp_artist, spotify.ImageSize.NORMAL)
        link_mock.assert_called_once_with(sp_link=sp_link)
        self.assertEqual(result, mock.sentinel.link)

    @mock.patch('spotify.Link', spec=spotify.Link)
    def test_link_creates_link_to_artist(self, link_mock, lib_mock):
        sp_artist = spotify.ffi.new('int *')
        artist = spotify.Artist(sp_artist=sp_artist)
        sp_link = spotify.ffi.new('int *')
        lib_mock.sp_link_create_from_artist.return_value = sp_link
        link_mock.return_value = mock.sentinel.link

        result = artist.link

        link_mock.assert_called_once_with(sp_link=sp_link)
        self.assertEqual(result, mock.sentinel.link)


@mock.patch('spotify.artist.lib', spec=spotify.lib)
class ArtistBrowserTest(unittest.TestCase):

    def create_session(self, lib_mock):
        session = mock.sentinel.session
        session._sp_session = mock.sentinel.sp_session
        spotify.session_instance = session
        return session

    def tearDown(self):
        spotify.session_instance = None

    def test_create_without_artist_or_sp_artistbrowse_fails(self, lib_mock):
        self.assertRaises(AssertionError, spotify.ArtistBrowser)

    def test_create_from_artist(self, lib_mock):
        session = self.create_session(lib_mock)
        sp_artist = spotify.ffi.new('int *')
        artist = spotify.Artist(sp_artist=sp_artist)
        sp_artistbrowse = spotify.ffi.new('int *')
        lib_mock.sp_artistbrowse_create.return_value = sp_artistbrowse

        result = artist.browse()

        lib_mock.sp_artistbrowse_create.assert_called_with(
            session._sp_session, sp_artist,
            int(spotify.ArtistBrowserType.FULL), mock.ANY, mock.ANY)
        # TODO Assert on callback stuff
        self.assertIsInstance(result, spotify.ArtistBrowser)

    def test_create_from_artist_with_type_and_callback(self, lib_mock):
        session = self.create_session(lib_mock)
        sp_artist = spotify.ffi.new('int *')
        artist = spotify.Artist(sp_artist=sp_artist)
        sp_artistbrowse = spotify.ffi.cast(
            'sp_artistbrowse *', spotify.ffi.new('int *'))
        lib_mock.sp_artistbrowse_create.return_value = sp_artistbrowse
        callback = mock.Mock()

        result = artist.browse(
            type=spotify.ArtistBrowserType.NO_TRACKS, callback=callback)

        lib_mock.sp_artistbrowse_create.assert_called_with(
            session._sp_session, sp_artist,
            int(spotify.ArtistBrowserType.NO_TRACKS), mock.ANY, mock.ANY)
        artistbrowse_complete_cb = (
            lib_mock.sp_artistbrowse_create.call_args[0][3])
        userdata = lib_mock.sp_artistbrowse_create.call_args[0][4]
        artistbrowse_complete_cb(sp_artistbrowse, userdata)

        result.complete_event.wait(3)
        callback.assert_called_with(result)

    def test_browser_is_gone_before_callback_is_called(self, lib_mock):
        self.create_session(lib_mock)
        sp_artist = spotify.ffi.new('int *')
        artist = spotify.Artist(sp_artist=sp_artist)
        sp_artistbrowse = spotify.ffi.cast(
            'sp_artistbrowse *', spotify.ffi.new('int *'))
        lib_mock.sp_artistbrowse_create.return_value = sp_artistbrowse
        callback = mock.Mock()

        result = spotify.ArtistBrowser(artist=artist, callback=callback)
        complete_event = result.complete_event
        result = None  # noqa
        tests.gc_collect()

        # FIXME The mock keeps the handle/userdata alive, thus the artist is
        # kept alive, and this test doesn't test what it is intended to test.
        artistbrowse_complete_cb = (
            lib_mock.sp_artistbrowse_create.call_args[0][3])
        userdata = lib_mock.sp_artistbrowse_create.call_args[0][4]
        artistbrowse_complete_cb(sp_artistbrowse, userdata)

        complete_event.wait(3)
        self.assertEqual(callback.call_count, 1)
        self.assertEqual(
            callback.call_args[0][0]._sp_artistbrowse, sp_artistbrowse)

    def test_adds_ref_to_sp_artistbrowse_when_created(self, lib_mock):
        sp_artistbrowse = spotify.ffi.new('int *')

        spotify.ArtistBrowser(sp_artistbrowse=sp_artistbrowse)

        lib_mock.sp_artistbrowse_add_ref.assert_called_with(sp_artistbrowse)

    @unittest.skip(
        'FIXME Becomes flaky in combination with '
        'test_create_from_artist_with_callback')
    def test_releases_sp_artistbrowse_when_artist_dies(self, lib_mock):
        sp_artistbrowse = spotify.ffi.new('int *')

        browser = spotify.ArtistBrowser(sp_artistbrowse=sp_artistbrowse)
        browser = None  # noqa
        tests.gc_collect()

        lib_mock.sp_artistbrowse_release.assert_called_with(sp_artistbrowse)

    @mock.patch('spotify.Link', spec=spotify.Link)
    def test_repr(self, link_mock, lib_mock):
        sp_artistbrowse = spotify.ffi.new('int *')
        browser = spotify.ArtistBrowser(sp_artistbrowse=sp_artistbrowse)
        sp_artist = spotify.ffi.new('int *')
        lib_mock.sp_artistbrowse_artist.return_value = sp_artist
        link_instance_mock = link_mock.return_value
        link_instance_mock.uri = 'foo'

        result = repr(browser)

        self.assertEqual(result, 'ArtistBrowser(%r)' % 'foo')

    def test_is_loaded(self, lib_mock):
        lib_mock.sp_artistbrowse_is_loaded.return_value = 1
        sp_artistbrowse = spotify.ffi.new('int *')
        browser = spotify.ArtistBrowser(sp_artistbrowse=sp_artistbrowse)

        result = browser.is_loaded

        lib_mock.sp_artistbrowse_is_loaded.assert_called_once_with(
            sp_artistbrowse)
        self.assertTrue(result)

    @mock.patch('spotify.utils.load')
    def test_load(self, load_mock, lib_mock):
        sp_artistbrowse = spotify.ffi.new('int *')
        browser = spotify.ArtistBrowser(sp_artistbrowse=sp_artistbrowse)

        browser.load(10)

        load_mock.assert_called_with(browser, timeout=10)

    def test_error(self, lib_mock):
        lib_mock.sp_artistbrowse_error.return_value = int(
            spotify.ErrorType.OTHER_PERMANENT)
        sp_artistbrowse = spotify.ffi.new('int *')
        browser = spotify.ArtistBrowser(sp_artistbrowse=sp_artistbrowse)

        result = browser.error

        lib_mock.sp_artistbrowse_error.assert_called_once_with(sp_artistbrowse)
        self.assertIs(result, spotify.ErrorType.OTHER_PERMANENT)

    def test_backend_request_duration(self, lib_mock):
        lib_mock.sp_artistbrowse_backend_request_duration.return_value = 137
        sp_artistbrowse = spotify.ffi.new('int *')
        browser = spotify.ArtistBrowser(sp_artistbrowse=sp_artistbrowse)

        result = browser.backend_request_duration

        lib_mock.sp_artistbrowse_backend_request_duration.assert_called_with(
            sp_artistbrowse)
        self.assertEqual(result, 137)

    def test_backend_request_duration_when_not_loaded(self, lib_mock):
        lib_mock.sp_artistbrowse_is_loaded.return_value = 0
        sp_artistbrowse = spotify.ffi.new('int *')
        browser = spotify.ArtistBrowser(sp_artistbrowse=sp_artistbrowse)

        result = browser.backend_request_duration

        lib_mock.sp_artistbrowse_is_loaded.assert_called_with(sp_artistbrowse)
        self.assertEqual(
            lib_mock.sp_artistbrowse_backend_request_duration.call_count, 0)
        self.assertIsNone(result)

    def test_artist(self, lib_mock):
        sp_artistbrowse = spotify.ffi.new('int *')
        browser = spotify.ArtistBrowser(sp_artistbrowse=sp_artistbrowse)
        sp_artist = spotify.ffi.new('int *')
        lib_mock.sp_artistbrowse_artist.return_value = sp_artist

        result = browser.artist

        self.assertIsInstance(result, spotify.Artist)
        self.assertEqual(result._sp_artist, sp_artist)

    @mock.patch('spotify.track.lib', spec=spotify.lib)
    def test_tracks(self, track_lib_mock, lib_mock):
        sp_track = spotify.ffi.cast('sp_track *', spotify.ffi.new('int *'))
        lib_mock.sp_artistbrowse_num_tracks.return_value = 1
        lib_mock.sp_artistbrowse_track.return_value = sp_track
        sp_artistbrowse = spotify.ffi.new('int *')
        browser = spotify.ArtistBrowser(sp_artistbrowse=sp_artistbrowse)

        self.assertEqual(lib_mock.sp_artistbrowse_add_ref.call_count, 1)
        result = browser.tracks
        self.assertEqual(lib_mock.sp_artistbrowse_add_ref.call_count, 2)

        self.assertEqual(len(result), 1)
        lib_mock.sp_artistbrowse_num_tracks.assert_called_with(sp_artistbrowse)

        item = result[0]
        self.assertIsInstance(item, spotify.Track)
        self.assertEqual(item._sp_track, sp_track)
        self.assertEqual(lib_mock.sp_artistbrowse_track.call_count, 1)
        lib_mock.sp_artistbrowse_track.assert_called_with(sp_artistbrowse, 0)
        track_lib_mock.sp_track_add_ref.assert_called_with(sp_track)

    def test_tracks_if_no_tracks(self, lib_mock):
        lib_mock.sp_artistbrowse_num_tracks.return_value = 0
        sp_artistbrowse = spotify.ffi.new('int *')
        browser = spotify.ArtistBrowser(sp_artistbrowse=sp_artistbrowse)

        result = browser.tracks

        self.assertEqual(len(result), 0)
        lib_mock.sp_artistbrowse_num_tracks.assert_called_with(sp_artistbrowse)
        self.assertEqual(lib_mock.sp_artistbrowse_track.call_count, 0)

    def test_tracks_if_unloaded(self, lib_mock):
        lib_mock.sp_artistbrowse_is_loaded.return_value = 0
        sp_artistbrowse = spotify.ffi.new('int *')
        browser = spotify.ArtistBrowser(sp_artistbrowse=sp_artistbrowse)

        result = browser.tracks

        lib_mock.sp_artistbrowse_is_loaded.assert_called_with(sp_artistbrowse)
        self.assertEqual(len(result), 0)

    @mock.patch('spotify.track.lib', spec=spotify.lib)
    def test_tophit_tracks(self, track_lib_mock, lib_mock):
        sp_track = spotify.ffi.cast('sp_track *', spotify.ffi.new('int *'))
        lib_mock.sp_artistbrowse_num_tophit_tracks.return_value = 1
        lib_mock.sp_artistbrowse_tophit_track.return_value = sp_track
        sp_artistbrowse = spotify.ffi.new('int *')
        browser = spotify.ArtistBrowser(sp_artistbrowse=sp_artistbrowse)

        self.assertEqual(lib_mock.sp_artistbrowse_add_ref.call_count, 1)
        result = browser.tophit_tracks
        self.assertEqual(lib_mock.sp_artistbrowse_add_ref.call_count, 2)

        self.assertEqual(len(result), 1)
        lib_mock.sp_artistbrowse_num_tophit_tracks.assert_called_with(
            sp_artistbrowse)

        item = result[0]
        self.assertIsInstance(item, spotify.Track)
        self.assertEqual(item._sp_track, sp_track)
        self.assertEqual(lib_mock.sp_artistbrowse_tophit_track.call_count, 1)
        lib_mock.sp_artistbrowse_tophit_track.assert_called_with(
            sp_artistbrowse, 0)
        track_lib_mock.sp_track_add_ref.assert_called_with(sp_track)

    def test_tophit_tracks_if_no_tracks(self, lib_mock):
        lib_mock.sp_artistbrowse_num_tophit_tracks.return_value = 0
        sp_artistbrowse = spotify.ffi.new('int *')
        browser = spotify.ArtistBrowser(sp_artistbrowse=sp_artistbrowse)

        result = browser.tophit_tracks

        self.assertEqual(len(result), 0)
        lib_mock.sp_artistbrowse_num_tophit_tracks.assert_called_with(
            sp_artistbrowse)
        self.assertEqual(lib_mock.sp_artistbrowse_track.call_count, 0)

    def test_tophit_tracks_if_unloaded(self, lib_mock):
        lib_mock.sp_artistbrowse_is_loaded.return_value = 0
        sp_artistbrowse = spotify.ffi.new('int *')
        browser = spotify.ArtistBrowser(sp_artistbrowse=sp_artistbrowse)

        result = browser.tophit_tracks

        lib_mock.sp_artistbrowse_is_loaded.assert_called_with(sp_artistbrowse)
        self.assertEqual(len(result), 0)

    def test_biography(self, lib_mock):
        sp_artistbrowse = spotify.ffi.new('int *')
        browser = spotify.ArtistBrowser(sp_artistbrowse=sp_artistbrowse)
        biography = spotify.ffi.new('char[]', b'Lived, played, and died')
        lib_mock.sp_artistbrowse_biography.return_value = biography

        result = browser.biography

        self.assertIsInstance(result, utils.text_type)
        self.assertEqual(result, 'Lived, played, and died')


class ArtistBrowserTypeTest(unittest.TestCase):

    def test_has_constants(self):
        self.assertEqual(spotify.ArtistBrowserType.FULL, 0)
        self.assertEqual(spotify.ArtistBrowserType.NO_TRACKS, 1)
        self.assertEqual(spotify.ArtistBrowserType.NO_ALBUMS, 2)
