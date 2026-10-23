#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Modified 2026-10-22 by weewx-packages: compatibility and tracker repairs.
# Modified 2026-10-23 by weewx-packages: retry network errors, report missing
# and unknown options instead of stopping WeeWX.
# Modified 2026-10-23 by weewx-packages: treat the installer placeholders as
# missing options, log through the logging module instead of syslog.

"""
Sends WeeWX weather records to Graphite using the Carbon/TCP protocol.

Source:: https://github.com/ampledata/weewx_graphite

Reference WeeWX Record format:
# {
#   'daily_rain': 0.0,
#   'wind_average': 3.5007240370967794,
#   'outHumidity': 83.62903225806451,
#   'heatindex': 61.59999999999994,
#   'day_of_year': 36.0,
#   'inTemp': 61.59999999999994,
#   'windGustDir': 200.470488,
#   'barometer': 30.238869061178168,
#   'windchill': 61.59999999999994,
#   'dewpoint': 56.59074077611711,
#   'rain': 0.0,
#   'pressure': 30.076167509542763,
#   'long_term_rain': 1.900000000000002,
#   'minute_of_day': 1348.0,
#   'altimeter': 30.230564691725238,
#   'usUnits': 1,
#   'interval': 5,
#   'dateTime': 1417218600.0,
#   'windDir': 187.7616636785259,
#   'outTemp': 61.59999999999994,
#   'windSpeed': 3.804394058064512,
#   'inHumidity': 83.62903225806451,
#   'windGust': 6.21371
# }
#
"""


__version__ = '2.2.0'
__author__ = 'Greg Albrecht W2GMD <oss@undef.net>'
__license__ = 'Apache License, Version 2.0'
__copyright__ = 'Copyright 2016 Orion Labs, Inc.'


import inspect
import logging
import queue
import socket
import sys
import time

import weewx
import weewx.restx
import weeutil.weeutil

log = logging.getLogger(__name__)

# install.py writes these values for host and port. Until the user replaces
# them, they count as missing, as 'replace_me' does for the WeeWX uploaders.
PLACEHOLDERS = ('CARBON_HOST', 'CARBON_PORT')


class Graphite(weewx.restx.StdRESTful):
    """
    Sends WeeWX weather records to Graphite using the Carbon/TCP protocol.
    """

    def __init__(self, engine, config_dict):
        super(Graphite, self).__init__(engine, config_dict)
        # get_site_dict() returns None, and logs why, when the section is
        # missing or has enable = false.
        _graphite_dict = weewx.restx.get_site_dict(config_dict, 'Graphite')
        if _graphite_dict is None:
            return
        for option in ('host', 'port'):
            if not _graphite_dict.get(option) or _graphite_dict[option] in PLACEHOLDERS:
                log.error("Data will not be posted: Missing option %s", option)
                return

        # GraphiteThread takes the options as keyword arguments. An option it
        # does not know would raise TypeError and stop WeeWX, so log it and
        # leave it out.
        _known = set(inspect.signature(GraphiteThread.__init__).parameters)
        _known -= {'self', 'queue', 'manager_dict'}
        for option in sorted(set(_graphite_dict) - _known):
            log.warning("Unknown option '%s' ignored", option)
            del _graphite_dict[option]

        _manager_dict = weewx.manager.get_manager_dict(
            config_dict['DataBindings'],
            config_dict['Databases'],
            'wx_binding'
        )

        self.archive_queue = queue.Queue()
        self.archive_thread = GraphiteThread(
            self.archive_queue,
            _manager_dict,
             **_graphite_dict
        )
        self.archive_thread.start()
        self.bind(weewx.NEW_ARCHIVE_RECORD, self.new_archive_record)

        log.info("Data will be sent to host %s:%s",
                 _graphite_dict['host'], _graphite_dict['port'])

    def new_archive_record(self, event):
        self.archive_queue.put(event.record)


class GraphiteThread(weewx.restx.RESTThread):

    """
    Thread for sending WeeWX Weather Data to Graphite.
    """

    DEFAULT_HOST = 'localhost'
    DEFAULT_PORT = '2003'
    DEFAULT_PREFIX = 'weewx'
    DEFAULT_POST_INTERVAL = 300
    DEFAULT_TIMEOUT = 60
    DEFAULT_MAX_TRIES = 3
    DEFAULT_RETRY_WAIT = 5

    def __init__(self, queue, manager_dict,
                 host=DEFAULT_HOST, port=DEFAULT_PORT, prefix=DEFAULT_PREFIX,
                 skip_upload=False, post_interval=DEFAULT_POST_INTERVAL,
                 max_backlog=sys.maxsize, stale=None, log_success=True,
                 log_failure=True, timeout=DEFAULT_TIMEOUT,
                 max_tries=DEFAULT_MAX_TRIES, retry_wait=DEFAULT_RETRY_WAIT):

        """Initialize an instances of GraphiteThread.

        :param host: Graphite Carbon Host.
        :param port: Graphite Carbon Port.
        :param prefix: Graphite Queue Prefix.
        :param log_success: Log a successful post in the system log.
        :param log_failure: Log an unsuccessful post in the system log.
        :param max_backlog: Max length of Queue before trimming. dft=sys.maxsize
        :param max_tries: How many times to try the post before giving up.
        :param stale: How old a record can be and still considered useful.
        :param post_interval: The interval in seconds between posts.
        :param timeout: How long to wait for the server to respond before fail.
        :param skip_upload: Debugging option to display data but do not upload.
        """
        super(GraphiteThread, self).__init__(
            queue,
            protocol_name='Graphite',
            manager_dict=manager_dict,
            post_interval=post_interval,
            max_backlog=max_backlog,
            stale=stale,
            log_success=log_success,
            log_failure=log_failure,
            timeout=timeout,
            max_tries=max_tries,
            retry_wait=retry_wait
        )

        self.host = host
        self.port = port
        self.prefix = prefix
        self.skip_upload = weeutil.weeutil.to_bool(skip_upload)

    def collect_metric(self, name, value, timestamp):
        if self.prefix:
            metric_name = '.'.join([self.prefix, name])
        else:
            metric_name = name

        if value is None:
            return
        payload = ('%s %f %d\n' % (metric_name, value, timestamp)).encode('utf-8')
        with socket.create_connection((self.host, int(self.port)), self.timeout) as sock:
            sock.sendall(payload)

    def process_record(self, record, dbmanager):
        _ = dbmanager

        if self.skip_upload:
            log.debug("skip_upload=True, skipping upload")
        else:
            # Each metric goes over its own connection, so an attempt can fail
            # after some metrics were sent. The retry sends the whole record
            # again. Whisper keeps the last value written for a metric and
            # timestamp, so the repeated metrics overwrite the earlier ones.
            _error = None
            for _count in range(self.max_tries):
                try:
                    if _count:
                        time.sleep(self.retry_wait)
                    for rkey, rval in record.items():
                        self.collect_metric(rkey, rval, record['dateTime'])
                    return
                except OSError as e:
                    self.handle_exception(e, _count + 1)
                    _error = e
            raise weewx.restx.FailedPost(
                "Failed upload after %d tries: %s" % (self.max_tries, _error))
