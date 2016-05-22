import feedparser
import os
from datetime import datetime
import time
from calendar import timegm
from dateutil.tz import tzlocal
import pytz
import logging
from urllib import urlretrieve
from urlparse import urlparse
from progress import Progress
LOCAL_TIMEZONE = pytz.timezone(datetime.now(tzlocal()).tzname())

class Vodcast:
    def __init__(self, item):
        self.title = item.title
        self.url = self._parse_video_url(item.enclosures)
        self.local_filename = self._generate_local_filename(self.url)

        self.updated = datetime.utcfromtimestamp(timegm(item.updated_parsed))
        
        self.description = item.description

        self._underlying_item = item

    def _parse_video_url(self, enclosures):
        video = enclosures[0]
        if 'video/mp4' == video.type:
            return video.href
        if 'video/mpeg' == video.type:
            return video.href
        if 'video/x-mp4' == video.type:
            return video.href
        raise Exception('cannot parse url from enclosure [%s]. unknown type: %s' % (video, video.type))

    def _generate_local_filename(self, link):
        return os.path.basename(urlparse(link).path)

    def __str__(self):
        return '%s(name=%s, url=%s, updated=%s)' % (self.__class__, self.local_filename, self.url, self.updated)
    def __repr__(self):
        return str(self)
    def __eq__(self, other):
        same = True
        same &= self.title == other.title
        same &= self.url == other.url
        same &= self.updated == other.updated
        return same

class DownloadProgressHook:
    def __init__(self, name, interval=1, *args, **kwargs):
        self.log = logging.getLogger('DownloadProgressHook')
        self.actual = 0
        self.interval = interval
        
    def report_hook(self, block_number, block_size, total_size):

            if block_number:
                self._eat(block_size)
            else:
                self._start_reporting(total_size)
                
            if time.time() - self.last_report > self.interval:
                self._log_report()
                self.last_report = time.time()
                
    def _eat(self, count):
        self.log.debug('eating %d bytes [%d/%d]' % (count, self.actual, self.total))
        self.actual += count
        self.eta_calculator.update(self.actual)

    def _start_reporting(self, total):
        self.total = total
        self.eta_calculator = Progress(self.total, unit = 'kb')
        self.last_report = time.time()

    def _log_report(self):
        self.log.info('%02.1f%% [%.0f/%.0f kb]. eta %ds (%dkb/s)' % (self.eta_calculator.percentage(), 
                                        self.actual / 1024, self.total / 1024, 
                                        self.eta_calculator.time_remaining(),
                                        self.eta_calculator.predicted_rate() / 1024))

class VodcastDownloader:
    def __init__(self, basedir=None, url_retriever = urlretrieve):
        self.basedir = basedir
        self.log = logging.getLogger('VodcastDownloader')
        self.report_log = logging.getLogger('report')
        self.url_retriever = url_retriever

    def __copy_stream_to_target(self, url, target_filename):
        if(os.path.exists(target_filename)):
            self.log.warn('skipping already existing file [%s]' % target_filename)
            return

        self.log.debug('downloading [%s] to [%s].', url, target_filename)
        
        download_reporter = DownloadProgressHook(target_filename)
        
        try:
            self.url_retriever(url, target_filename, download_reporter.report_hook)
        except Exception as e:
            self.__remove_file_if_exists(target_filename, e)
            raise
        except KeyboardInterrupt:
            self.__remove_file_if_exists(target_filename, 'User interrupted')
            raise Exception('User interrupted')

    def __remove_file_if_exists(self, filename, exception):
        if(os.path.exists(filename)):
            self.log.warn('removing file [%s] after exception: %s' % (filename, str(exception)))
            os.unlink(filename)

    def should_be_downloaded(self, vodcast, reference_date):
        """
        check if a vodcast should be downloaded with respect to a reference date. 
        
        Vodcast dates are assumed to be in UTC (see feedparser._parse_rfc822_date), whereas reference_data is assumed to be in local time
        """
        local_vodcast_date = pytz.utc.localize(vodcast.updated).astimezone(LOCAL_TIMEZONE)
        local_reference_date = reference_date
        self.log.debug('checking if [%s] should be downloaded (%s > %s): %s (in timezone [%s])', vodcast, local_vodcast_date, local_reference_date, local_vodcast_date > local_reference_date, LOCAL_TIMEZONE)
        return local_vodcast_date > local_reference_date

    def _create_target_filename(self, vodcast):
        target_filename = os.path.join(self.basedir, vodcast.local_filename)
        return target_filename

    def download(self, vodcast):
        target_filename = self._create_target_filename(vodcast)
        vodcast.target_filename = target_filename
        self.report_log.info('%(target_filename)s(%(updated)s) - %(url)s - %(description)s' % vodcast.__dict__)
        self.__copy_stream_to_target(vodcast.url, target_filename)
        return target_filename


class VodcastDownloadManager:
    def __init__(self, rss_feed_or_url, download_dir, threads=1):
        self.downloader = VodcastDownloader(download_dir)
        self.log = logging.getLogger('DownloadManager')
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
        return counter


def parse_video_item(item):
    return Vodcast(item)

