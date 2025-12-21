"""Battery control engine for EVCC EVOpt Scheduler."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Dict, Iterable, Optional

from .ha_client import HomeAssistantServiceClient


@dataclass
class BatteryControlConfig:
    """Config for a single controllable battery."""

    name: str
    strategy: str
    result_index: int
    min_soc_percent: float
    max_soc_percent: float
    ha_service: str
    ha_service_data: Dict[str, Any]
    context: Dict[str, Any]


class BatteryController:
    """Orchestrates battery control based on EVOpt output."""

    def __init__(
        self,
        batteries: Iterable[BatteryControlConfig],
        client: Optional[HomeAssistantServiceClient],
        logger: logging.Logger,
    ) -> None:
        self._configs = list(batteries)
        self._client = client
        self._log = logger.getChild("battery")
        if not self._configs:
            self._log.info("No battery profiles configured; control loop disabled")

    def _render_payload(self, data: Any, context: Dict[str, Any]) -> Any:
        if isinstance(data, dict):
            return {key: self._render_payload(value, context) for key, value in data.items()}
        if isinstance(data, list):
            return [self._render_payload(item, context) for item in data]
        if isinstance(data, str):
            try:
                return data.format(**context)
            except Exception:  # pragma: no cover - keep original
                return data
        return data

    def _extract_result(self, response: Dict[str, Any], index: int) -> Dict[str, Any]:
        batteries = response.get("batteries") or []
        if 0 <= index < len(batteries):
            return batteries[index] or {}
        return {}

    def _extract_evcc_battery(self, evcc_state: Dict[str, Any], index: int) -> Dict[str, Any]:
        batteries = evcc_state.get("battery") or []
        if 0 <= index < len(batteries):
            return batteries[index] or {}
        return {}

    async def apply(self, response: Dict[str, Any], evcc_state: Dict[str, Any]) -> None:
        if not self._client or not self._configs:
            return

        for cfg in self._configs:
            context: Dict[str, Any] = {"battery": cfg.name, **cfg.context}
            result = self._extract_result(response, cfg.result_index)
            evcc_battery = self._extract_evcc_battery(evcc_state, cfg.result_index)

            charging = (result.get("charging_power") or [0])
            discharging = (result.get("discharging_power") or [0])
            soc_series = (result.get("state_of_charge") or [None])

            charge_power = float(charging[0]) if charging else 0.0
            discharge_power = float(discharging[0]) if discharging else 0.0
            target_power = charge_power - discharge_power

            soc = soc_series[0]
            if soc is None:
                soc = evcc_battery.get("soc")
            context.update(
                {
                    "target_power": target_power,
                    "charge_power": charge_power,
                    "discharge_power": discharge_power,
                    "soc": soc,
                    "strategy": cfg.strategy,
                }
            )

            mode = self._determine_mode(cfg, soc, target_power)
            context["mode"] = mode

            payload = self._render_payload(cfg.ha_service_data, context)
            try:
                await self._client.call_service(cfg.ha_service, payload)
            except Exception as err:  # pragma: no cover - logged
                self._log.error("Failed to call service for battery %s: %s", cfg.name, err)

    def _determine_mode(
        self,
        cfg: BatteryControlConfig,
        soc: Optional[float],
        target_power: float,
    ) -> str:
        min_soc = cfg.min_soc_percent
        max_soc = cfg.max_soc_percent

        if cfg.strategy == "fixed_charge":
            if soc is not None and soc >= max_soc:
                return "idle"
            return "charge"

        if cfg.strategy == "fixed_discharge":
            if soc is not None and soc <= min_soc:
                return "idle"
            return "discharge"

        # grid_balancing or default
        if soc is not None:
            if soc <= min_soc and target_power <= 0:
                return "charge"
            if soc >= max_soc and target_power >= 0:
                return "discharge"

        if target_power > 0:
            return "charge"
        if target_power < 0:
            return "discharge"
        return "idle"
