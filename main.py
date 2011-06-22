import logging
import logging.config
from optparse import OptionParser
from rss.rss_feed_downloader import VodcastDownloadManager
from datetime import datetime, timedelta
import hashlib
from os import path
from urlparse import urlparse

LAST_FETCHED_FILE_TEMPLATE = 'last_feed_access_%(hostname)s_%(hash)s.timestamp'

def _create_fetch_info_path(base, identity):
    return path.join(base, LAST_FETCHED_FILE_TEMPLATE % {
                                                'hash' : hashlib.sha224(identity).hexdigest(),
                                                'hostname' : urlparse(identity).hostname
                                                })

def _determineReferenceDate(download_directory, day_offset, identity):
    if not day_offset:
        try:
            with open(_create_fetch_info_path(download_directory, identity), 'r') as lastFetched:
                reference_date = datetime.strptime(lastFetched.read(), '%c')
        except IOError, e:
            print 'failed to read last updated timestamp. falling back to day_offset: %s' % e
            day_offset = 7
    if day_offset:
        reference_date = datetime.now()
        reference_date -= timedelta(days=day_offset)
            
    return reference_date

def _saveLastFetchedTimestamp(download_directory, identity):
    with open(_create_fetch_info_path(download_directory, identity), 'w') as lastFetched:
        lastFetched.write(datetime.strftime(datetime.now(), '%c'))
        
def _checked_load_logging_config(config_path):
    expanded_config_path = path.expanduser(config_path)
    if not path.exists(expanded_config_path):
        raise Exception("failed to locate a logging configuration at [%s]. please check the location" % expanded_config_path)
    logging.config.fileConfig(expanded_config_path)
        
def main(args):
    parser = OptionParser()
    parser.add_option("-u", "--url", dest="rss_url",
                      help="download vodcasts from feed URL", metavar="URL")
    parser.add_option("-d", "--download-directory", dest="download_directory",
                      help="save vodcasts in DIR", metavar="DIR")
    parser.add_option("-o", "--day-offset", dest="day_offset",
                      help="only download vodcasts DAYS old or younger",
                      metavar="DAYS", type="int", default=None)
    parser.add_option("-t", "--threads", dest="threads",
                      help="how many THREADS to use for download",
                      metavar="THREADS", type="int", default=1)
    parser.add_option("-v", "--verbose",
                      action="count", dest="verbose",
                      help="print status messages to stdout more verbose")

    (options, args) = parser.parse_args()

    if not (options.rss_url and options.download_directory):
        parser.error('url and directory are required')
        
    if not path.isdir(options.download_directory):
        parser.error('[%s] is not a directory' % options.download_directory)

    if options.verbose > 1:
        _checked_load_logging_config("~/.python/logging_debug.conf")
    elif options.verbose:
        _checked_load_logging_config("~/.python/logging.conf")
    else:
        logging.basicConfig(stream=sys.stdout, level=logging.WARN)

    vdm = VodcastDownloadManager(options.rss_url, options.download_directory, options.threads)

    reference_date = _determineReferenceDate(options.download_directory, options.day_offset, options.rss_url)
    vdm.download_all_newer(reference_date)
    _saveLastFetchedTimestamp(options.download_directory, options.rss_url)


if __name__ == '__main__':
    import sys
    main(sys.argv)
