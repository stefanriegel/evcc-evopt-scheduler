"""Sensor entities for the EVCC EVOpt Scheduler integration."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.const import ENERGY_WATT_HOUR, PERCENTAGE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import EvccEvoptDataCoordinator


@dataclass
class EvccSensorDescription(SensorEntityDescription):
    """Describe a scheduler sensor."""

    value_fn: Callable[[Dict[str, Any]], Any]
    attr_fn: Optional[Callable[[Dict[str, Any]], Optional[Dict[str, Any]]]] = None


SENSORS: tuple[EvccSensorDescription, ...] = (
    EvccSensorDescription(
        key="status",
        name="EVOpt Status",
        value_fn=lambda data: data.get("status"),
    ),
    EvccSensorDescription(
        key="objective_value",
        name="EVOpt Objective Value",
        value_fn=lambda data: data.get("objective_value"),
    ),
    EvccSensorDescription(
        key="grid_import_total",
        name="EVOpt Grid Import Total",
        native_unit_of_measurement=ENERGY_WATT_HOUR,
        value_fn=lambda data: data.get("grid_import_total"),
    ),
    EvccSensorDescription(
        key="grid_export_total",
        name="EVOpt Grid Export Total",
        native_unit_of_measurement=ENERGY_WATT_HOUR,
        value_fn=lambda data: data.get("grid_export_total"),
    ),
    EvccSensorDescription(
        key="battery_soc",
        name="EVCC Battery SoC",
        native_unit_of_measurement=PERCENTAGE,
        value_fn=lambda data: data.get("battery_soc"),
    ),
)


async def async_setup_platform(
    hass: HomeAssistant,
    config: Dict[str, Any],
    async_add_entities: AddEntitiesCallback,
    discovery_info: Optional[Dict[str, Any]] = None,
) -> None:
    """Set up the sensors using the shared coordinator."""
    coordinator: EvccEvoptDataCoordinator | None = hass.data.get(DOMAIN)
    if coordinator is None:
        return

    entities = [EvccEvoptSensor(coordinator, description) for description in SENSORS]
    async_add_entities(entities)


class EvccEvoptSensor(CoordinatorEntity[EvccEvoptDataCoordinator], SensorEntity):
    """Representation of a scheduler sensor."""

    entity_description: EvccSensorDescription

    def __init__(self, coordinator: EvccEvoptDataCoordinator, description: EvccSensorDescription) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_name = description.name
        self._attr_unique_id = f"{DOMAIN}_{description.key}"

    @property
    def native_value(self) -> Any:
        data = self.coordinator.data or {}
        return self.entity_description.value_fn(data)

    @property
    def extra_state_attributes(self) -> Optional[Dict[str, Any]]:
        data = self.coordinator.data or {}
        if self.entity_description.attr_fn:
            return self.entity_description.attr_fn(data)
        if raw := data.get("raw"):
            return {"has_raw": True, "response_keys": list(raw.get("response", {}).keys())}
        return None
