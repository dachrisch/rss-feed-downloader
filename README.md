RSS Feed Downloader
===================

download vodcasts from RSS feeds

usage
-----

python main.py [options]

Options:
  -h, --help            show this help message and exit
  -u URL, --url=URL     download vodcasts from feed URL
  -d DIR, --download-directory=DIR
                        save vodcasts in DIR
  -o DAYS, --day-offset=DAYS
                        only download vodcasts DAYS old or younger
  -t THREADS, --threads=THREADS
                        how many THREADS to use for download
  -v, --verbose         print status messages to stdout more verbose

dependencies
------------

feedparser - parsing rss feeds - www.feedparser.org
 
restrictions
------------

currently only runs in *nix like environments (Linux, cygwin, etc.)