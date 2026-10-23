WeeWX observations for Graphite
==============================

Send numeric archive observations to Graphite Carbon over plaintext TCP.
Metrics retain the original archive timestamp and the archive's units.

This is the weewx-packages continuation, release **2.2.0**. See `ORIGIN.md
<ORIGIN.md>`_ and `REPAIR_NOTES.md <REPAIR_NOTES.md>`_. The catalog archive
targets WeeWX >=5.5.2,<5.7 and Python >=3.10,<3.15. Earlier upstream branches
for WeeWX 2.7 and 3 remain historical references, not this release's target.

Installation
------------

You need a reachable Carbon plaintext TCP listener, usually on port 2003,
and WeeWX. The runtime has no additional Python dependencies.

Install the fixed release with stock WeeWX 5::

    weectl extension install https://github.com/weewx-packages/weewx-graphite/releases/download/v2.2.0/weewx-graphite-2.2.0.tar.gz --config /path/to/weewx.conf

Use the WeeWX Python environment and replace the configuration path. You
can also download that URL and install its local archive. Use elevated
permissions only when your station files require them.

The installer registers ``user.graphite.Graphite``. Set the Carbon listener
in ``weewx.conf``::

    [StdRESTful]
        [[Graphite]]
            host = graphite.example.com
            port = 2003
            prefix = weewx.garden

Restart WeeWX yourself. After an archive record, look for metrics below
``weewx.garden`` on your Graphite server. ``post_interval`` defaults to 300
seconds. The service resolves ``wx_binding`` at startup.


Usage
-----
Numeric archive fields appear under ``weewx.*`` unless ``prefix`` changes
the path. Missing values are skipped; zero is sent. The uploader includes
metadata fields such as ``usUnits``. It has no unit conversion, TLS or
authentication settings. The receiver must accept Carbon plaintext TCP.


Example
-------
  .. image:: https://dl.dropboxusercontent.com/u/4036736/Screenshots/pressure_temp.png


Author
------
Greg Albrecht W2GMD <oss@undef.net>


Copyright
---------
Copyright 2016 Orion Labs, Inc.


License
-------
Apache License, Version 2.0. See LICENSE.


Source
------
https://github.com/ampledata/weewx_graphite

Retention and unwanted station paths
-----------------------------------

The extension sends Carbon plaintext with each archive record's original Unix
timestamp. Graphite stores the history; Grafana selects the display range.
If recent points appear but older points do not, query Graphite directly over
the same epoch range and inspect Carbon's storage-schemas.conf retention and
storage-aggregation.conf settings. The uploader cannot restore data already
expired by Graphite retention.

The configured prefix defaults to weewx. It is a metric path prefix, not a
Graphite server or a station registry. Stop that prefix's writer before
removing its backend data. On a Whisper-backed Carbon installation, locate
the configured LOCAL_DATA_DIR; the prefix maps to directories containing .wsp
files there. Other Graphite storage backends have their own deletion tools.
The extension neither creates nor deletes server-side station registrations.

Legacy installer configuration
------------------------------

WeeWX 4 and earlier require the restful_services option to exist before
installing a REST extension. If installation reports KeyError for that key,
add an empty option to the existing Engine/Services section and retry::

    [Engine]
        [[Services]]
            restful_services =

Keep any existing services in that option. WeeWX 5 creates missing service
lists automatically. The continuation uses weecfg.extension.ExtensionInstaller
and Python 3; it has no dependency on the unrelated PyPI setup package.

Modified 2026-10-22 by weewx-packages.
