"""Sensor platform for EVOpt integration."""
import logging
from typing import Any, Dict

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType

from . import EVOptDataUpdateCoordinator
from .const import DOMAIN, NAME_SHORT
from .entity import EVOptEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up sensor entities."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]

    entities = [
        EVOptStatusSensor(coordinator, config_entry),
        EVOptOptimizationStatusSensor(coordinator, config_entry),
        EVOptObjectiveValueSensor(coordinator, config_entry),
        EVOptBatteryCountSensor(coordinator, config_entry),
        EVOptGridImportTotalSensor(coordinator, config_entry),
        EVOptGridExportTotalSensor(coordinator, config_entry),
    ]

    async_add_entities(entities)


class EVOptStatusSensor(EVOptEntity, SensorEntity):
    """EVOpt service status sensor."""

    _attr_name = f"{NAME_SHORT} Status"
    _attr_unique_id = "status"

    @property
    def native_value(self) -> StateType:
        """Return the state of the sensor."""
        if self.coordinator.data:
            status = self.coordinator.data.get("status", "unknown")
            if status == "healthy":
                return "online"
            elif status == "error":
                return "offline"
            else:
                return status
        return "unknown"

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Return the state attributes."""
        if self.coordinator.data:
            health_data = self.coordinator.data.get("health", {})
            return {
                "health_status": health_data.get("status"),
                "health_message": health_data.get("message"),
                "last_update": self.coordinator.data.get("last_update"),
            }
        return {}


class EVOptOptimizationStatusSensor(EVOptEntity, SensorEntity):
    """EVOpt optimization status sensor."""

    _attr_name = f"{NAME_SHORT} Optimization Status"
    _attr_unique_id = "optimization_status"

    @property
    def native_value(self) -> StateType:
        """Return the optimization status."""
        if self.coordinator.data:
            return self.coordinator.data.get("optimization_status", "unknown")
        return "unknown"


class EVOptObjectiveValueSensor(EVOptEntity, SensorEntity):
    """EVOpt objective value sensor."""

    _attr_name = f"{NAME_SHORT} Objective Value"
    _attr_unique_id = "objective_value"
    _attr_native_unit_of_measurement = "currency"
    _attr_device_class = "monetary"

    @property
    def native_value(self) -> StateType:
        """Return the objective value."""
        if self.coordinator.data:
            return self.coordinator.data.get("objective_value")
        return None


class EVOptBatteryCountSensor(EVOptEntity, SensorEntity):
    """EVOpt battery count sensor."""

    _attr_name = f"{NAME_SHORT} Battery Count"
    _attr_unique_id = "battery_count"
    _attr_native_unit_of_measurement = "batteries"

    @property
    def native_value(self) -> StateType:
        """Return the battery count."""
        if self.coordinator.data:
            return self.coordinator.data.get("battery_count", 0)
        return 0


class EVOptGridImportTotalSensor(EVOptEntity, SensorEntity):
    """EVOpt total grid import sensor."""

    _attr_name = f"{NAME_SHORT} Grid Import Total"
    _attr_unique_id = "grid_import_total"
    _attr_native_unit_of_measurement = "Wh"
    _attr_device_class = "energy"

    @property
    def native_value(self) -> StateType:
        """Return the total grid import."""
        if self.coordinator.data:
            return self.coordinator.data.get("grid_import_total", 0)
        return 0


class EVOptGridExportTotalSensor(EVOptEntity, SensorEntity):
    """EVOpt total grid export sensor."""

    _attr_name = f"{NAME_SHORT} Grid Export Total"
    _attr_unique_id = "grid_export_total"
    _attr_native_unit_of_measurement = "Wh"
    _attr_device_class = "energy"

    @property
    def native_value(self) -> StateType:
        """Return the total grid export."""
        if self.coordinator.data:
            return self.coordinator.data.get("grid_export_total", 0)
        return 0