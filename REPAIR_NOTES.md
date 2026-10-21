# Repair validation

Version 2.2.0. Original repository and revision are in ORIGIN.md.

* https://github.com/ampledata/weewx_graphite/issues/4: Installer imports weecfg.extension. Isolated install passes on WeeWX 4/5. WeeWX 4 core still requires Engine/Services/restful_services to exist; reproduced missing-key failure and tested documented empty-option recovery.
* https://github.com/ampledata/weewx_graphite/issues/3: Documented prefix and configured Carbon LOCAL_DATA_DIR/Whisper deletion process. Actual backend/path on reporter server not knowable from extension config.
* https://github.com/ampledata/weewx_graphite/issues/2: Local Carbon receiver proves original archive timestamps are sent. Documented retention/range checks. Historical retention and Grafana datasource configuration on reporter server require its logs/configuration.
* https://github.com/ampledata/weewx_graphite/issues/1: Current source already uses accumulateLeaves rather than removed get_dict. Service initialization tested on WeeWX 4/5; Python 3 queue/socket handling repaired.

Tests run under WeeWX 4.10.2/5.1.0 on Python 3.10 and WeeWX 5.5.2 on Python 3.14. Local receivers and isolated install directories avoid live station changes. The tests do not establish individual external account permissions.
