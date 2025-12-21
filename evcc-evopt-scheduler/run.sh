#!/usr/bin/with-contenv bashio
# shellcheck shell=bash
set -euo pipefail

bashio::log.info "Starting EVCC EVOpt Scheduler add-on"

cd /opt/evcc_evopt_scheduler || bashio::exit.nok "Application directory missing"
exec python3 ./app/main.py
