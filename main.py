import logging
import logging.config
from optparse import OptionParser
from rss.rss_feed_downloader import VodcastDownloadManager
from datetime import datetime, timedelta

def main(args):
    parser = OptionParser()
    parser.add_option("-u", "--url", dest="rss_url",
                      help="download vodcasts from feed URL", metavar="URL")
    parser.add_option("-d", "--download-directory", dest="download_directory",
                      help="save vodcasts in DIR", metavar="DIR")
    parser.add_option("-o", "--day-offset", dest="day_offset",
                      help="only download vodcasts DAYS old or younger", 
                      metavar="DAYS", type="int", default=7)
    parser.add_option("-t", "--threads", dest="threads",
                      help="how many THREADS to use for download", 
                      metavar="THREADS", type="int", default=1)
    parser.add_option("-v", "--verbose",
                      action="count", dest="verbose",
                      help="print status messages to stdout more verbose")

    (options, args) = parser.parse_args()

    if not (options.rss_url and options.download_directory):
        parser.error('url and directory are required')

    if options.verbose > 1:
        logging.config.fileConfig("/home/cda/.python/logging_debug.conf")
    elif options.verbose:
        logging.config.fileConfig("/home/cda/.python/logging.conf")
    else:
        logging.basicConfig(stream=sys.stdout, level=logging.WARN)

    vdm = VodcastDownloadManager(options.rss_url, options.download_directory, options.threads)

    reference_date = datetime.now()
    reference_date -= timedelta(days=options.day_offset)
    vdm.download_all_newer(reference_date)


if __name__ == '__main__':
    import sys
    main(sys.argv)
