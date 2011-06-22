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

requirements
------------

feedparser - parsing rss feeds - www.feedparser.org

a logging configuration in '~/.python/logging.conf'

example:

    [formatters]
    keys: detailed,simple
     
    [handlers]
    keys: console
     
    [loggers]
    keys: root
     
    [formatter_simple]
    format: %(name)s:%(levelname)s:  %(message)s
     
    [formatter_detailed]
    format: %(name)s:%(levelname)s %(module)s:%(lineno)d:  %(message)s
     
    [handler_console]
    class: StreamHandler
    args: []
    formatter: simple
    
    [logger_root]
    level: INFO
    handlers: console

 
restrictions
------------

currently only runs in *nix like environments (Linux, cygwin, etc.)