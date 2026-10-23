# WeeWX Graphite uploader

Sends every archive record to a Graphite Carbon receiver over plaintext TCP.
Each metric keeps the archive record's timestamp and the archive's units. The
uploader does no unit conversion and has no TLS or authentication settings.

This is the weewx-packages continuation of
[ampledata/weewx_graphite](https://github.com/ampledata/weewx_graphite). See
[ORIGIN.md](ORIGIN.md) and [REPAIR_NOTES.md](REPAIR_NOTES.md).

## Requirements

- A Graphite Carbon receiver that accepts the plaintext protocol over TCP,
  usually on port 2003.
- No Python packages beyond WeeWX and the standard library.

## Installation

Install `graphite` from the [WeeWX packages catalog](https://github.com/weewx-packages/catalog/blob/main/packages/graphite.md).
The catalog page lists the current release, its WeeWX and Python
requirements, and the install, update and removal commands.

The installer adds `user.graphite.Graphite` to `restful_services` and writes
a `[[Graphite]]` section with the placeholders `CARBON_HOST` and
`CARBON_PORT`. Replace both, then restart WeeWX.

## Configuration

```ini
[StdRESTful]
    [[Graphite]]
        host = graphite.example.com
        port = 2003
        prefix = weewx.garden
```

After the next archive record, metrics appear below `weewx.garden` on the
Graphite server.

| Option | Default | Meaning |
|---|---|---|
| `host` | required | Carbon host. |
| `port` | required | Carbon plaintext TCP port, usually `2003`. |
| `prefix` | `weewx` | Metric path prefix. An empty value sends the bare field names. |
| `post_interval` | `300` | Minimum seconds between two uploaded records. |
| `timeout` | `60` | Socket timeout in seconds. |
| `stale` | none | Records older than this many seconds are skipped. |
| `max_backlog` | unlimited | Queue length before old records are dropped. |
| `log_success` | `True` | Log each uploaded record. |
| `log_failure` | `True` | Log failed uploads. |
| `skip_upload` | `False` | Process records without sending them. |

Every field of the archive record becomes one metric named
`<prefix>.<field>`, including `dateTime`, `usUnits` and `interval`. Fields
without a value are skipped. Zero is sent. The service always reads the
`wx_binding` data binding.

The prefix is only a metric path. It does not register a station on the
server. To remove a station's data, stop its writer first. On a
Whisper-backed Carbon installation the prefix maps to directories of `.wsp`
files below the configured `LOCAL_DATA_DIR`. Other Graphite storage backends
have their own deletion tools.

## Limitations

- A missing `host` or `port` stops WeeWX at startup with a `KeyError`.
  Options other than those in the table, such as `enable`, stop it with a
  `TypeError`.
- `max_tries` and `retry_wait` are accepted but have no effect. If the
  Carbon receiver cannot be reached, the upload thread logs the error and
  ends. Uploads resume after a WeeWX restart.
- Graphite retention decides how much history is kept. If recent points
  appear but older ones do not, query Graphite directly for the same epoch
  range. Then check the retention in Carbon's `storage-schemas.conf` and
  `storage-aggregation.conf`. The uploader cannot restore expired data.
- Older WeeWX installers stop with a `KeyError` when
  `[Engine][[Services]]` has no `restful_services` option. Add an empty
  option, keep any existing services in it, and install again:

  ```ini
  [Engine]
      [[Services]]
          restful_services =
  ```

- The tests use local receivers. They do not replace a check against a real
  Graphite server.

## Development

```sh
python -m pytest -q tests
```

Run the tests in an environment with WeeWX and pytest.

## License

Copyright 2016 Orion Labs, Inc. Written by Greg Albrecht W2GMD
<oss@undef.net>.

Apache License, Version 2.0. See [LICENSE](LICENSE).

Modified 2026-10-23 by weewx-packages.
