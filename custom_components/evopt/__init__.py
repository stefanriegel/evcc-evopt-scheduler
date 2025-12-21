"""EVOpt integration for Home Assistant."""
import asyncio
import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import config_validation as config_val
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN, NAME, PLATFORMS, STARTUP_MESSAGE, SERVICE_RUN_OPTIMIZATION
from .api import EVOptApiClient
from .service import EVOptService

_LOGGER: logging.Logger = logging.getLogger(__package__)

SCAN_INTERVAL = timedelta(seconds=30)

CONFIG_SCHEMA = config_val.removed(DOMAIN, raise_if_present=False)


async def async_migrate_entry(hass: HomeAssistant, config_entry: ConfigEntry):
    """Migrate old entry."""
    _LOGGER.debug("Migrating from version %s", config_entry.version)
    return True


async def async_setup(hass: HomeAssistant, config: dict):  # pylint: disable=unused-argument
    """Set up this integration using YAML is not supported."""
    return True


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry):
    """Set up this integration from a config entry."""
    if DOMAIN not in hass.data:
        _LOGGER.info(STARTUP_MESSAGE)

    # Create API client
    session = async_get_clientsession(hass)
    client = EVOptApiClient(
        host=config_entry.data["host"],
        session=session,
    )

    # Test the API connection
    try:
        await client.async_health_check()
    except Exception as err:
        raise ConfigEntryNotReady(f"Could not connect to EVOpt API: {err}") from err

    # Create data coordinator
    coordinator = EVOptDataUpdateCoordinator(hass, client, config_entry)
    await coordinator.async_refresh()

    if not coordinator.last_update_success:
        raise ConfigEntryNotReady

    # Store coordinator
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][config_entry.entry_id] = coordinator

    # Forward entry setup to platforms
    await hass.config_entries.async_forward_entry_setups(config_entry, PLATFORMS)

    # Register services
    evopt_service = EVOptService(hass, config_entry, coordinator)
    hass.services.async_register(
        DOMAIN,
        SERVICE_RUN_OPTIMIZATION,
        evopt_service.run_optimization,
    )

    config_entry.async_on_unload(config_entry.add_update_listener(entry_update_listener))

    return True


async def async_unload_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(config_entry, PLATFORMS)

    if unload_ok:
        hass.data[DOMAIN].pop(config_entry.entry_id)
        # Unregister services
        hass.services.async_remove(DOMAIN, SERVICE_RUN_OPTIMIZATION)

    return unload_ok


async def entry_update_listener(hass: HomeAssistant, config_entry: ConfigEntry) -> None:
    """Update listener for config entry changes."""
    await hass.config_entries.async_reload(config_entry.entry_id)


class EVOptDataUpdateCoordinator(DataUpdateCoordinator):
    """Data update coordinator for EVOpt."""

    def __init__(self, hass: HomeAssistant, client: EVOptApiClient, config_entry: ConfigEntry):
        """Initialize coordinator."""
        self.client = client
        self.config_entry = config_entry

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=SCAN_INTERVAL,
        )

    async def _async_update_data(self):
        """Fetch data from EVOpt API."""
        try:
            # Get optimization status from API client
            status_data = await self.client.async_get_optimization_status()
            if status_data is None:
                raise UpdateFailed("No data received from EVOpt API")

            # Return the actual data structure
            return {
                "health": status_data.get("health_data", {}),
                "status": status_data.get("status", "unknown"),
                "optimization_status": status_data.get("optimization_status", "unknown"),
                "objective_value": status_data.get("objective_value"),
                "battery_count": status_data.get("battery_count", 0),
                "grid_import_total": status_data.get("grid_import_total", 0),
                "grid_export_total": status_data.get("grid_export_total", 0),
                "last_update": status_data.get("last_update"),
            }
        except Exception as err:
            _LOGGER.warning("Error fetching data from EVOpt: %s", err)
            raise UpdateFailed from err