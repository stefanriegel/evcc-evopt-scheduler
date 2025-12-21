"""API client for EVOpt."""
import asyncio
import logging
from typing import Any, Dict, Optional

import aiohttp
from aiohttp import ClientConnectorError, ClientResponseError

_LOGGER = logging.getLogger(__name__)


class EVOptApiClient:
    """API client for EVOpt service."""

    def __init__(self, host: str, session: aiohttp.ClientSession) -> None:
        """Initialize the API client."""
        self.host = host.rstrip("/")
        self.session = session
        self._timeout = aiohttp.ClientTimeout(total=10)

    async def async_health_check(self) -> Dict[str, Any]:
        """Check if EVOpt service is healthy."""
        try:
            async with self.session.get(
                f"{self.host}/optimize/health",
                timeout=self._timeout
            ) as response:
                response.raise_for_status()
                return await response.json()
        except (ClientConnectorError, ClientResponseError, asyncio.TimeoutError) as err:
            _LOGGER.error("Error checking EVOpt health: %s", err)
            raise

    async def async_get_optimization_status(self) -> Optional[Dict[str, Any]]:
        """Get current optimization status/results."""
        try:
            # Get health status first
            health = await self.async_health_check()

            # For now, return health data with placeholders for optimization data
            # In a full implementation, this would fetch the last optimization result
            # or current system state from EVOpt
            return {
                "status": health.get("status", "unknown"),
                "message": health.get("message", ""),
                "health_data": health,
                "optimization_status": "unknown",  # Would come from actual optimization result
                "objective_value": None,  # Economic benefit from optimization
                "battery_count": 0,  # Number of batteries in system
                "grid_import_total": 0,  # Total grid import
                "grid_export_total": 0,  # Total grid export
                "last_update": None,  # Timestamp of last optimization
            }
        except Exception as err:
            _LOGGER.error("Error getting optimization status: %s", err)
            return {
                "status": "error",
                "message": f"Connection failed: {err}",
                "health_data": None,
                "optimization_status": "error",
                "objective_value": None,
                "battery_count": 0,
                "grid_import_total": 0,
                "grid_export_total": 0,
                "last_update": None,
            }

    async def async_optimize_charge_schedule(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Request charge schedule optimization."""
        try:
            async with self.session.post(
                f"{self.host}/optimize/charge-schedule",
                json=data,
                timeout=aiohttp.ClientTimeout(total=30)  # Longer timeout for optimization
            ) as response:
                response.raise_for_status()
                return await response.json()
        except (ClientConnectorError, ClientResponseError, asyncio.TimeoutError) as err:
            _LOGGER.error("Error requesting optimization: %s", err)
            return None