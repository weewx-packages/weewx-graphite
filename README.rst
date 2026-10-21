weewx\_graphite - WeeWX Extension for sending weather data to Graphite.
=======================================================================

Note
----

There are two versions of this Extension:

1. weewx_graphite version 1.x for WeeWX 2.7.x: https://github.com/ampledata/weewx_graphite/tree/compat27
2. weewx_graphite version 2.x for WeeWX 3.x: https://github.com/ampledata/weewx_graphite/

This continuation is tested with WeeWX 4.10.2 and 5.x on Python 3.

Installation
------------

1. Download tarball from Github:
    ``wget https://github.com/weewx-packages/weewx-graphite/archive/master.tar.gz``
2. Install with WeeWX's Extension Manager:
    ``weectl extension install master.tar.gz`` (WeeWX 5), or
    ``wee_extension --install master.tar.gz`` (WeeWX 4).
3. Update **weewx.conf** to point to your Graphite **host** and **port**::

      [StdRESTful]
        [[Graphite]]
            host = graphite.example.com
            port = 2003

4. Restart WeeWX.


Usage
-----
Number-like metrics collected by WeeWX will show up in Graphite under the
**weewx.*** node (unless reconfigured with the ``prefix`` config paramater).


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
