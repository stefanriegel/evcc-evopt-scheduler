"""Constants for the EVCC EVOpt Scheduler integration."""
from __future__ import annotations

from datetime import timedelta

DOMAIN = "evcc_evopt_scheduler"
CONF_SHARE_PATH = "share_path"
DEFAULT_SHARE_PATH = "/share/evcc-evopt-scheduler"
DEFAULT_SCAN_INTERVAL = timedelta(seconds=30)
