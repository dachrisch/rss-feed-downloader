import feedparser
from datetime import datetime
import os
import sys
import unittest
import pytz
from dateutil.tz import tzlocal
sys.path.insert(0,os.path.abspath(__file__+"/../.."))
from rss.rss_feed_downloader import parse_video_item
from rss.rss_feed_downloader import VodcastDownloader
from rss.rss_feed_downloader import VodcastDownloadManager
from rss.rss_feed_downloader import Vodcast
import tempfile

def as_local_datetime(date):
    local_timezone = pytz.timezone('Europe/Berlin')
    return local_timezone.localize(date)

class ItemMock:
    class EnclosureMock:
        pass
    def __init__(self, title, date, url):
        self.title = title 
        self.updated_parsed = date 
        self.description = 'unused'
        enclosure = ItemMock.EnclosureMock()
        enclosure.type = 'video/mp4'
        enclosure.href = url
        self.enclosures = [enclosure]

class VodcastFeedDownloaderTest(unittest.TestCase):
    
    def setUp(self):
        # d = feedparser.parse('http://www.daserste.de/podcasts/mam_dyn~id,434~weltspiegel.xml')
        # d = feedparser.parse('http://www.ndr.de/podcast/extradrei196.xml')
        self.rss_feed = feedparser.parse(r'''<?xml version='1.0' encoding='UTF-8'?>
                            <rss version='2.0'>
                            <channel>
                            <title>Extra3</title>
                            <item>
                            <title>Extra 3 one</title>
                            <description>Tatort Taliban; Jasmin trifft: Frau zu Guttenberg</description>
                            <pubDate>Tue, 26 Oct 2010 11:53:49 +0200</pubDate>
                            <enclosure url='http://media.ndr.de/download/podcasts/extradrei196/TV-20101023-2220-5801.h264.mp4' type='video/mp4' />
                            <guid isPermaLink='false'>TV-20101023-2220-5801-V</guid>
                            <link>http://media.ndr.de/download/podcasts/extradrei196/TV-20101023-2220-5801.h264.mp4</link>
                            </item></channel></rss>''')

    def __create_tempfile(self, content):
        testfile = tempfile.NamedTemporaryFile(delete = False)
        testfile.write(content)
        testfile.close()
        return testfile
    
    def assertFilePresent(self, basedir, filename, remove_after_check = False):
        expected_filename = os.path.join(basedir, filename)
        self.assertTrue(os.path.exists(expected_filename), '"%s" does not exists' % expected_filename)
        if remove_after_check:
            os.remove(expected_filename)

    def assertFileNotPresent(self, basedir, filename):
        expected_filename = os.path.join(basedir, filename)
        self.assertFalse(os.path.exists(expected_filename), '''"%s" exists but it shouldn't''' % expected_filename)

    def test_givenRssFeedWhenVodcastFormatThenEntriesWithVideosContainedAreParsed(self):
        entries = self.rss_feed.entries
        vodcast = parse_video_item(entries[0])

        self.assertEqual(vodcast.title, 'Extra 3 one')
        self.assertEqual(vodcast.url, 'http://media.ndr.de/download/podcasts/extradrei196/TV-20101023-2220-5801.h264.mp4')
        self.assertEqual(vodcast.local_filename, 'TV-20101023-2220-5801.h264.mp4')
        self.assertEqual(vodcast.updated, datetime(2010, 10, 26, 9, 53, 49))

    def test_givenVideoUrlWithParametersWhenGeneratingLocalFileThenParametersAreStriped(self):
        entry = type('Entry', (object,), {}) 
        entry.title = 'test_givenVideoUrlWithParametersWhenGeneratingLocalFileThenParametersAreStriped'
        entry.enclosures = (type('Enclosure', (object,), {})  , )
        entry.enclosures[0].type = 'video/mp4'
        entry.enclosures[0].href = 'TV-20101023-2220-5801.h264.mp4?should_be_removed'
        entry.updated_parsed = (2010, 10, 26, 10, 53, 49, 0, 0, 0)
        entry.description = 'for test only'
        vodcast = parse_video_item(entry)

        self.assertEqual(vodcast.local_filename, 'TV-20101023-2220-5801.h264.mp4')

    def test_givenUrlPointingToLocalResourceWhenDownloadedThenContentWillBeStored(self):
        entries = self.rss_feed.entries
        vodcast = parse_video_item(entries[0])
        
        tempdir = tempfile.mkdtemp()

        vodcast_downloader = VodcastDownloader(tempdir)
        
        testfile = self.__create_tempfile('vodcast content')
        
        vodcast.url = 'file://' + testfile.name

        vodcast_downloader.download(vodcast)
        
        self.assertFilePresent(tempdir, vodcast.local_filename, remove_after_check = True)
        
        os.remove(testfile.name)
        os.rmdir(tempdir)
        
    def test_givenNoInternetConnectionWhenDownloadingFeedThenTimestampWillNotBeUpdated(self):
        self.assertEqual(VodcastDownloadManager(None, "").download_all_newer(None), 0)
        
    def test_givenRssWithVodcastsWhenDownloadingThenOnlyNewFilesWillBeDownloaded(self):
        entries = self.rss_feed.entries
        vodcast = parse_video_item(entries[0])
        
        vodcast_downloader = VodcastDownloader()

        self.assertTrue(vodcast_downloader.should_be_downloaded(vodcast, as_local_datetime(datetime(2010, 10, 25, 11, 53, 49))), vodcast.updated)
        self.assertFalse(vodcast_downloader.should_be_downloaded(vodcast, as_local_datetime(datetime(2010, 10, 27, 11, 53, 49))), vodcast.updated)
        
    def test_givenFeedWithSomeVodcastsWhenReferenceDateGivenThenAllNewerFeedsWillBeDownloaded(self):
        feed_content = r'''<?xml version='1.0' encoding='UTF-8'?>
                            <rss version='2.0'>
                            <channel>
                            <title>Extra3</title>
                            <item>
                                <title>Extra 3 one</title>
                                <description>Tatort Taliban; Jasmin trifft: Frau zu Guttenberg</description>
                                <pubDate>Tue, 26 Oct 2010 11:53:49 +0200</pubDate>
                                <enclosure url='http://media.ndr.de/download/podcasts/extradrei196/TV-20101063-2220-5801.h264.mp4' type='video/mp4' />
                                <guid isPermaLink='false'>TV-20101026-2220-5801-V</guid>
                                <link>http://media.ndr.de/download/podcasts/extradrei196/TV-20101026-2220-5801.h264.mp4</link>
                            </item>
                            <item>
                                <title>Extra 3 two</title>
                                <description>Tatort Taliban; Jasmin trifft: Frau zu Guttenberg</description>
                                <pubDate>Tue, 27 Oct 2010 11:53:49 +0200</pubDate>
                                <enclosure url='http://media.ndr.de/download/podcasts/extradrei196/TV-20101027-2220-5801.h264.mp4' type='video/mp4' />
                                <guid isPermaLink='false'>TV-20101027-2220-5801-V</guid>
                                <link>http://media.ndr.de/download/podcasts/extradrei196/TV-20101027-2220-5801.h264.mp4</link>
                            </item>
                            <item>
                                <title>Extra 3 three</title>
                                <description>Tatort Taliban; Jasmin trifft: Frau zu Guttenberg</description>
                                <pubDate>Tue, 28 Oct 2010 11:53:49 +0200</pubDate>
                                <enclosure url='http://media.ndr.de/download/podcasts/extradrei196/TV-20101028-2220-5801.h264.mp4' type='video/mp4' />
                                <guid isPermaLink='false'>TV-20101028-2220-5801-V</guid>
                                <link>http://media.ndr.de/download/podcasts/extradrei196/TV-20101028-2220-5801.h264.mp4</link>
                            </item>
                            </channel></rss>'''

        vodcast_download_manager = VodcastDownloadManager(feed_content, None)
        
        vocast_collector = []
        downloader = VodcastDownloader(None)
        downloader.download = lambda vodcast: vocast_collector.append(vodcast)
        vodcast_download_manager.downloader = downloader

        vodcast_download_manager.download_all_newer(as_local_datetime(datetime(2010, 10, 27, 0, 0, 0)))
        self.assertNotIn(Vodcast(ItemMock('Extra 3 one', (2010, 10, 26, 9, 53, 49), 'http://media.ndr.de/download/podcasts/extradrei196/TV-20101026-2220-5801.h264.mp4'))
                      , vocast_collector)
        self.assertIn(Vodcast(ItemMock('Extra 3 two', (2010, 10, 27, 9, 53, 49), 'http://media.ndr.de/download/podcasts/extradrei196/TV-20101027-2220-5801.h264.mp4'))
                      , vocast_collector)
        self.assertIn(Vodcast(ItemMock('Extra 3 three', (2010, 10, 28, 9, 53, 49), 'http://media.ndr.de/download/podcasts/extradrei196/TV-20101028-2220-5801.h264.mp4'))
                      , vocast_collector)

    def test_saveAndLoadTimeInFile(self):
        dateFile = self.__create_tempfile(datetime.strftime(datetime(2010, 10, 27, 0, 0, 0), '%c'))
        
        with open(dateFile.name, 'r') as f:
            timestamp = datetime.strptime(f.read(), '%c')
            
        self.assertEqual(timestamp, datetime(2010, 10, 27, 0, 0, 0))
    def test_create_md5_hash(self):
        import hashlib
        self.assertEqual( hashlib.sha224("http://some.domain/rss.xml").hexdigest(), '28dbff3e80675af61e810c911d19ce690d2497a03f64d47f5559199e')
        
    def test_parse_date(self):
        from calendar import timegm
        date = feedparser._parse_date_rfc822('Tue, 28 Oct 2010 11:53:49 +0200')
        assert 1288259629 == timegm(date), timegm(date)
        assert datetime(2010, 10, 28, 9, 53, 49) == datetime.utcfromtimestamp(timegm(date)), datetime.utcfromtimestamp(timegm(date))
        
    def test_reference_data_in_local_time(self):
        entries = self.rss_feed.entries
        vodcast = parse_video_item(entries[0])
        
        vodcast_downloader = VodcastDownloader()

        self.assertEqual(vodcast.updated, datetime(2010, 10, 26, 9, 53, 49))
        berlin = pytz.timezone("Europe/Berlin")
        self.assertTrue(vodcast_downloader.should_be_downloaded(vodcast, berlin.localize(datetime(2010, 10, 26, 10, 53, 49))), vodcast.updated)

    def test_should_dete_file_during_exception(self):
        testfile = tempfile.mktemp()

        vodcast_downloader = VodcastDownloader()
        vodcast = Vodcast(ItemMock('Extra 3 three', (2010, 10, 28, 9, 53, 49), 'http://media.ndr.de/download/podcasts/extradrei196/TV-20101028-2220-5801.h264.mp4'))
        vodcast.local_filename = testfile
        
        def read_throwing_exception(url, filename, hoock):
            fd = open(filename, 'w')
            fd.close()
            self.assertFilePresent(None, filename)
            raise KeyboardInterrupt
        
        vodcast_downloader.url_retriever = read_throwing_exception
        
        self.assertRaisesRegexp(Exception, 'User interrupted' ,vodcast_downloader.download, vodcast)
        self.assertFileNotPresent(None, testfile)
        
    def test_create_timestamp_file_if_it_doesnt_exists_and_no_file_was_downloaded(self):
        from main import main as rss_main
        import main
        from optparse import OptionParser
        import sys
        def throwing_error(self, msg):
            raise Exception(msg)
        main.OptionParser = op = OptionParser
        op.error = throwing_error
        download_directory = tempfile.gettempdir()
        expected_filename = main._create_fetch_info_path(download_directory, 'localhost')
        try:
            self.assertFileNotPresent('', expected_filename)
            rss_main(['-d', download_directory, '-u', 'localhost'])
            self.assertFilePresent('', expected_filename)
        finally:
            os.unlink(expected_filename)

if __name__ == '__main__':
    import logging
    logging.basicConfig(filename = 'test_debug.log', level=logging.DEBUG)

    unittest.main()
