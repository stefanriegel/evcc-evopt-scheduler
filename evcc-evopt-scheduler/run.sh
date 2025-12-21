#!/usr/bin/with-contenv bashio
# shellcheck shell=bash
set -euo pipefail

bashio::log.info "Starting EVCC EVOpt Scheduler add-on"

exec python3 -m app.main
