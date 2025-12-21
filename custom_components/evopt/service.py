"""Services for EVOpt integration."""
import logging
from typing import Any, Dict

from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as config_val

from .const import SERVICE_RUN_OPTIMIZATION

_LOGGER = logging.getLogger(__name__)


class EVOptService:
    """EVOpt service handler."""

    def __init__(self, hass: HomeAssistant, config_entry, coordinator):
        """Initialize the service."""
        self.hass = hass
        self.config_entry = config_entry
        self.coordinator = coordinator

    async def run_optimization(self, call: ServiceCall) -> Dict[str, Any]:
        """Run optimization with provided parameters."""
        try:
            # Extract parameters from service call
            batteries = call.data.get("batteries", [])
            time_series = call.data.get("time_series", {})
            strategy = call.data.get("strategy", {})
            grid = call.data.get("grid", {})
            eta_c = call.data.get("eta_c", 0.95)
            eta_d = call.data.get("eta_d", 0.95)

            # Prepare optimization input
            optimization_input = {
                "batteries": batteries,
                "time_series": time_series,
                "eta_c": eta_c,
                "eta_d": eta_d,
            }

            if strategy:
                optimization_input["strategy"] = strategy
            if grid:
                optimization_input["grid"] = grid

            # Run optimization
            result = await self.coordinator.client.async_optimize_charge_schedule(optimization_input)

            if result:
                _LOGGER.info("Optimization completed successfully")
                return result
            else:
                _LOGGER.error("Optimization failed")
                return {"error": "Optimization failed"}

        except Exception as err:
            _LOGGER.error("Error running optimization: %s", err)
            return {"error": str(err)}