import feedparser
import os
import re
from threading import Thread, Event
from urllib2 import urlopen
from datetime import datetime
from etacalculator import EtaCalculator
import time
import logging

class Vodcast:
    def __init__(self, item):
        self.title = item.title
        self.url = self._parse_video_url(item.enclosures)
        self.local_filename = self._generate_local_filename(self.url)

        self.updated = datetime.fromtimestamp(time.mktime(item.updated_parsed))

        self._underlying_item = item

    def _parse_video_url(self, enclosures):
        video = enclosures[0]
        if 'video/mp4' == video.type:
            return video.href
        if 'video/mpeg' == video.type:
            return video.href
        raise Exception('cannot parse url from enclosure [%s]. unknown type: %s' % (video, video.type))

    def _generate_local_filename(self, link):
        return os.path.basename(link)

    def __str__(self):
        return '%s(name=%s, url=%s, updated=%s)' % (self.__class__, self.local_filename, self.url, self.updated)


class DownloadProgressThread(Thread):
    def __init__(self, name, total, interval=1, *args, **kwargs):
        Thread.__init__(self, name=name, *args, **kwargs)
        self.log = logging.getLogger('DownloadProgressThread')
        self.actual = 0
        self.total = total
        self.should_finish = Event()
        self.interval = interval
        self.eta_calculator = EtaCalculator(self.total)
        self.last_actual_kb = -100

    def eat(self, count):
        self.log.debug('eating %d bytes [%d/%d]' % (count, self.actual, self.total))
        self.actual += count
        self.eta_calculator.update(self.actual)

    def start_reporting(self):
        self.should_finish.clear()
        self.start()

    def stop_reporting(self):
        self.should_finish.set()

    def run(self):
        while not self.should_finish.is_set():
            self._log_report()
            self.should_finish.wait(self.interval)

    def _log_report(self):
        percentage_done = self.actual / float(self.total) * 100.0
        actual_kb = self.actual / 1024
        total_kb = self.total / 1024
        speed_kb = actual_kb - self.last_actual_kb
        download_rate = speed_kb / self.interval
        seconds_remaining = self.eta_calculator.eta
        self.log.info('%02.1f%% [%.0f/%.0f kb]. eta %ds (%dkb/s)' % (percentage_done, 
                                        actual_kb, total_kb, seconds_remaining,
                                        download_rate))
        self.last_actual_kb = actual_kb


class VodcastDownloader:
    chunk_size = 100 * 1024

    def __init__(self, basedir=None):
        self.basedir = basedir
        self.log = logging.getLogger('VodcastDownloader')

    def _remote_get_video(self, url):
        return urlopen(url)

    def __copy_stream_to_target(self, stream, target_filename):
        if(os.path.exists(target_filename)):
            self.log.warn('skipping already existing file [%s]' % target_filename)
            return

        m = re.search('Content-Length: (\d+)', str(stream.info()))
        if m:
            content_length = int(m.group(1))
        else:
            content_length = -1
            self.log.error('could not find "Content-Length" header. Is is really a video-stream? [%s]' % stream.info())

        self.log.debug('downloading [%s] (%d bytes) to [%s].', stream, content_length, target_filename)
        actual_read = DownloadProgressThread(target_filename, content_length)
        actual_read.start_reporting()

        target = open(target_filename, 'wb')
        try:
            with target:
                content = stream.read(VodcastDownloader.chunk_size)
                while content:
                    target.write(content)
                    actual_read.eat(len(content))
                    content = stream.read(VodcastDownloader.chunk_size)
            stream.close()
        except:
            os.remove(target_filename)
            raise
        finally:
            actual_read.stop_reporting()

    def should_be_downloaded(self, vodcast, reference_date):
        self.log.debug('checking if [%s] should be downloaded (> %s): %s', vodcast, reference_date, vodcast.updated > reference_date)
        return vodcast.updated > reference_date

    def download(self, vodcast):
        stream = self._remote_get_video(vodcast.url)

        target_filename = os.path.join(self.basedir, vodcast.local_filename)
        self.__copy_stream_to_target(stream, target_filename)
        return target_filename


class VodcastDownloadManager:
    def __init__(self, rss_feed_or_url, download_dir, threads=1):
        self.downloader = VodcastDownloader(download_dir)
        self.log = logging.getLogger('VodcastDownloader')
        self.threads = threads

        self.vodcasts = []
        self.log.info('parsing feed at [%s]...' % rss_feed_or_url)
        rss_feed = feedparser.parse(rss_feed_or_url)
        for entry in rss_feed.entries:
            self.log.debug('parsing rss item %s' % entry)
            vodcast = parse_video_item(entry)
            self.vodcasts.append(vodcast)
            self.log.debug('parsed vodcast %s' % vodcast)
        self.log.info('found %d vodcast entries.' % len(rss_feed.entries))

    def download_all_newer(self, reference_date):
        self.downloader.reference_date = reference_date
        vodcasts_to_download = []
        for vodcast in self.vodcasts:
            if self.downloader.should_be_downloaded(vodcast, reference_date):
                vodcasts_to_download.append(vodcast)

        self.log.info('will download [%d] vodcasts updated after [%s]' % (len(vodcasts_to_download), reference_date))

        counter = 0
        for vodcast_to_download in vodcasts_to_download:
            self.log.info('[%03d] downloading %s...' % (counter, vodcast_to_download))
            self.downloader.download(vodcast_to_download)
            counter += 1
        self.log.info('downloaded [%d] vodcasts' % counter)


def parse_video_item(item):
    return Vodcast(item)

