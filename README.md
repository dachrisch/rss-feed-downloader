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

contunious integration
----------------------
[![Build Status](https://secure.travis-ci.org/dachrisch/rss-feed-downloader.png?branch=master)](http://travis-ci.org/dachrisch/rss-feed-downloader)

CI provided by http://travis-ci.org/
requirements
------------

    pip install -r requirements.txt

a logging configuration in '~/.python/logging.conf'

example:

    [formatters]
    keys: detailed,simple,evenSimpler
     
    [handlers]
    keys: console
     
    [loggers]
    keys: root,report

    [formatter_evenSimpler]
    format: %(message)s
     
    [formatter_simple]
    format: %(name)s:%(levelname)s:  %(message)s
     
    [formatter_detailed]
    format: %(name)s:%(levelname)s %(module)s:%(lineno)d:  %(message)s
     
    [handler_console]
    class: StreamHandler
    args: [sys.out]
    formatter: simple

    [handler_report]
    class: FileHandler
    args: ['/path_to_logfile', 'a']
    formatter: evenSimpler
    
    [logger_root]
    level: INFO
    handlers: console

 
restrictions
------------

currently only runs in *nix like environments (Linux, cygwin, etc.)
