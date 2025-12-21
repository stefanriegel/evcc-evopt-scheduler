"""Data coordinator for EVCC EVOpt Scheduler integration."""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

_LOGGER = logging.getLogger(__name__)


class EvccEvoptDataCoordinator(DataUpdateCoordinator[Dict[str, Any]]):
    """Coordinator that loads the latest scheduler data from the share directory."""

    def __init__(self, hass: HomeAssistant, share_path: Path, update_interval) -> None:
        self._share_path = share_path
        super().__init__(
            hass,
            _LOGGER,
            name="evcc_evopt_scheduler",
            update_interval=update_interval,
        )

    def _load_json(self, filename: str) -> Dict[str, Any]:
        path = self._share_path / filename
        if not path.exists():
            return {}
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as err:
            raise UpdateFailed(f"Invalid JSON in {path}: {err}") from err
        except OSError as err:  # pragma: no cover - disk issues
            raise UpdateFailed(f"Failed to read {path}: {err}") from err

    async def _async_update_data(self) -> Dict[str, Any]:
        def _read_files() -> Dict[str, Any]:
            response = self._load_json("last_response.json")
            request = self._load_json("last_request.json")
            evcc_state = self._load_json("last_evcc_state.json")
            return self._build_payload(response, request, evcc_state)

        return await self.hass.async_add_executor_job(_read_files)

    def _build_payload(
        self, response: Dict[str, Any], request: Dict[str, Any], evcc_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        status = response.get("status") or request.get("status") or "unknown"
        objective_value = response.get("objective_value")
        grid_import = sum(response.get("grid_import", []) or [])
        grid_export = sum(response.get("grid_export", []) or [])

        battery_soc = evcc_state.get("batterySoc")
        site_power = evcc_state.get("sitePower")
        ev_status = evcc_state.get("vehicles", [])

        return {
            "status": status,
            "objective_value": objective_value,
            "grid_import_total": grid_import,
            "grid_export_total": grid_export,
            "battery_soc": battery_soc,
            "site_power": site_power,
            "ev_status": ev_status,
            "raw": {
                "response": response,
                "request": request,
                "evcc_state": evcc_state,
            },
        }
