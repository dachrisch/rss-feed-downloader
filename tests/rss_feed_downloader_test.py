import feedparser
from datetime import datetime
import os
import sys
import unittest
sys.path.insert(0,os.path.abspath(__file__+"/../.."))
from rss.rss_feed_downloader import parse_video_item, VodcastDownloader, VodcastDownloadManager

from urllib import urlretrieve

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
                            <pubDate>Tue, 26 Oct 2010 11:53:49</pubDate>
                            <enclosure url='http://media.ndr.de/download/podcasts/extradrei196/TV-20101023-2220-5801.h264.mp4' type='video/mp4' />
                            <guid isPermaLink='false'>TV-20101023-2220-5801-V</guid>
                            <link>http://media.ndr.de/download/podcasts/extradrei196/TV-20101023-2220-5801.h264.mp4</link>
                            </item></channel></rss>''')

    def __create_tempfile(self, content):
        import tempfile
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
        import pytz
        utc = pytz.timezone('UTC')
        entries = self.rss_feed.entries
        vodcast = parse_video_item(entries[0])

        self.assertEqual(vodcast.title, 'Extra 3 one')
        self.assertEqual(vodcast.url, 'http://media.ndr.de/download/podcasts/extradrei196/TV-20101023-2220-5801.h264.mp4')
        self.assertEqual(vodcast.local_filename, 'TV-20101023-2220-5801.h264.mp4')
        self.assertEqual(utc.localize(vodcast.updated), datetime(2010, 10, 26, 8, 53, 49, tzinfo = utc))

    def test_givenUrlPointingToLocalResourceWhenDownloadedThenContentWillBeStored(self):
        entries = self.rss_feed.entries
        vodcast = parse_video_item(entries[0])
        
        import tempfile
        
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

        self.assertTrue(vodcast_downloader.should_be_downloaded(vodcast, datetime(2010, 10, 25, 11, 53, 49)), vodcast.updated)
        self.assertFalse(vodcast_downloader.should_be_downloaded(vodcast, datetime(2010, 10, 27, 11, 53, 49)), vodcast.updated)
        
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
        import tempfile
        
        tempdir = tempfile.mkdtemp()
        vodcast_download_manager = VodcastDownloadManager(feed_content, tempdir)
        
        class FileMock:
            def __init__(self):
                self.eof = False
            def read(self, bytes = None):
                if self.eof:
                    return None
                self.eof = True
                return 'mock vodcast'
            def info(self):
                pass
            def close(self):
                pass
        local_file_mock = FileMock()
        
        vodcast_download_manager.downloader._remote_get_video = lambda url: local_file_mock

        vodcast_download_manager.download_all_newer(datetime(2010, 10, 27, 0, 0, 0))
        
        self.assertFileNotPresent(tempdir, 'TV-20101026-2220-5801.h264.mp4')
        self.assertFilePresent(tempdir, 'TV-20101027-2220-5801.h264.mp4', remove_after_check = True)
        self.assertFilePresent(tempdir, 'TV-20101028-2220-5801.h264.mp4', remove_after_check = True)
        os.rmdir(tempdir)

    def test_saveAndLoadTimeInFile(self):
        dateFile = self.__create_tempfile(datetime.strftime(datetime(2010, 10, 27, 0, 0, 0), '%c'))
        
        with open(dateFile.name, 'r') as f:
            timestamp = datetime.strptime(f.read(), '%c')
            
        self.assertEqual(timestamp, datetime(2010, 10, 27, 0, 0, 0))
    def test_create_md5_hash(self):
        import hashlib
        self.assertEqual( hashlib.sha224("http://some.domain/rss.xml").hexdigest(), '28dbff3e80675af61e810c911d19ce690d2497a03f64d47f5559199e')

if __name__ == '__main__':
    import logging
    logging.basicConfig(filename = 'test_debug.log', level=logging.DEBUG)

    unittest.main()
