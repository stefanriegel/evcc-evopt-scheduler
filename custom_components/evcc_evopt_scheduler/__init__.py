"""Home Assistant integration for the EVCC EVOpt Scheduler add-on."""
from __future__ import annotations

import json
import logging
from datetime import timedelta
from pathlib import Path
from typing import Any, Dict, Optional

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_SCAN_INTERVAL
from homeassistant.core import HomeAssistant
from homeassistant.helpers import discovery
from homeassistant.helpers.typing import ConfigType

from .const import CONF_SHARE_PATH, DEFAULT_SCAN_INTERVAL, DEFAULT_SHARE_PATH, DOMAIN
from .coordinator import EvccEvoptDataCoordinator

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Optional(CONF_SHARE_PATH, default=DEFAULT_SHARE_PATH): vol.Coerce(str),
                vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL.seconds): vol.All(
                    vol.Coerce(int), vol.Range(min=5)
                ),
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the integration from YAML configuration."""
    if DOMAIN not in config:
        return True

    domain_config = config[DOMAIN]
    share_path = Path(domain_config[CONF_SHARE_PATH])
    scan_interval = timedelta(seconds=domain_config[CONF_SCAN_INTERVAL])

    coordinator = EvccEvoptDataCoordinator(hass, share_path, scan_interval)
    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN] = coordinator

    hass.async_create_task(discovery.async_load_platform(hass, "sensor", DOMAIN, {}, config))

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """This integration does not use config entries."""
    _LOGGER.debug("No config entry support for %s", DOMAIN)
    return False


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    _LOGGER.debug("Nothing to unload for %s", DOMAIN)
    return True
