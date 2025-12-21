"""Base entity for EVOpt integration."""
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import EVOptDataUpdateCoordinator


class EVOptEntity(CoordinatorEntity[EVOptDataUpdateCoordinator], Entity):
    """Base entity for EVOpt."""

    def __init__(self, coordinator: EVOptDataUpdateCoordinator, config_entry) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)
        self.config_entry = config_entry
        self._attr_device_info = {
            "identifiers": {(config_entry.domain, config_entry.entry_id)},
            "name": "EVOpt",
            "manufacturer": "EVOpt",
            "model": "Charging Optimizer",
        }

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.last_update_success