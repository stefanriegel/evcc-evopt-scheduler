"""Main application entrypoint for the EVCC EVOpt Scheduler add-on."""
from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import aiohttp  # type: ignore
from aiohttp import web  # type: ignore
from dateutil import parser as date_parser  # type: ignore

try:  # Python 3.9+ standard module
    from zoneinfo import ZoneInfo
except ImportError:  # pragma: no cover
    from backports.zoneinfo import ZoneInfo  # type: ignore

CONFIG_PATH = Path("/data/options.json")
SHARE_DIR = Path("/share/evcc-evopt-scheduler")
DEFAULT_TIME_ZONE = "Europe/Berlin"
APP_PORT = 8000


@dataclass
class BatteryConfig:
    """Configuration options for the controlled battery."""

    charge_from_grid: bool
    discharge_to_grid: bool
    min_soc_percent: float
    max_soc_percent: float
    max_charge_power_w: float
    max_discharge_power_w: float


@dataclass
class BatteryDetails:
    """Resolved battery parameters used for the optimization payload."""

    device_id: str
    capacity_wh: float
    s_min: float
    s_max: float
    s_initial: float
    s_goal: float


@dataclass
class AppConfig:
    """Top-level configuration container."""

    evcc_url: str
    evopt_url: str
    time_zone: str
    time_frame_seconds: int
    optimization_horizon_hours: int
    evcc_poll_interval_seconds: int
    scheduler_interval_seconds: int
    grid_power_limit_w: float
    log_level: str
    battery: BatteryConfig

    @classmethod
    def load(cls, path: Path = CONFIG_PATH) -> "AppConfig":
        with path.open("r", encoding="utf-8") as handle:
            raw: Dict[str, Any] = json.load(handle)

        battery_raw = raw.get("battery", {})
        battery = BatteryConfig(
            charge_from_grid=bool(battery_raw.get("charge_from_grid", True)),
            discharge_to_grid=bool(battery_raw.get("discharge_to_grid", True)),
            min_soc_percent=float(battery_raw.get("min_soc_percent", 5)),
            max_soc_percent=float(battery_raw.get("max_soc_percent", 95)),
            max_charge_power_w=float(battery_raw.get("max_charge_power_w", 10000)),
            max_discharge_power_w=float(
                battery_raw.get("max_discharge_power_w", battery_raw.get("max_charge_power_w", 10000))
            ),
        )

        return cls(
            evcc_url=raw.get("evcc_url", "http://core-evcc:7070").rstrip("/"),
            evopt_url=raw.get("evopt_url", "http://core-evopt:7050").rstrip("/"),
            time_zone=raw.get("time_zone", DEFAULT_TIME_ZONE),
            time_frame_seconds=int(raw.get("time_frame_seconds", 900)),
            optimization_horizon_hours=int(raw.get("optimization_horizon_hours", 48)),
            evcc_poll_interval_seconds=int(raw.get("evcc_poll_interval_seconds", 15)),
            scheduler_interval_seconds=int(raw.get("scheduler_interval_seconds", 900)),
            grid_power_limit_w=float(raw.get("grid_power_limit_w", 11000)),
            log_level=raw.get("log_level", "INFO").upper(),
            battery=battery,
        )


@dataclass
class OptimizationSnapshot:
    """Stores the last optimization request/response details."""

    requested_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    payload: Optional[Dict[str, Any]] = None
    response: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

    def as_dict(self) -> Dict[str, Any]:
        return {
            "requested_at": self.requested_at.isoformat() if self.requested_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "error": self.error,
            "payload": self.payload,
            "response": self.response,
        }


class EvccClient:
    """Async HTTP client for retrieving EVCC state and forecasts."""

    def __init__(self, base_url: str, session: aiohttp.ClientSession, logger: logging.Logger) -> None:
        self._base_url = base_url
        self._session = session
        self._log = logger.getChild("evcc")

    async def fetch_state(self) -> Dict[str, Any]:
        url = f"{self._base_url}/api/state"
        try:
            async with self._session.get(url, timeout=15) as resp:
                resp.raise_for_status()
                data = await resp.json(loads=json.loads)
                self._log.debug("Fetched EVCC state")
                return data
        except Exception as err:  # pragma: no cover - logged and re-raised
            self._log.error("Failed to fetch EVCC state: %s", err)
            raise


class EvoptClient:
    """Async HTTP client for executing EVOpt optimizations."""

    def __init__(self, base_url: str, session: aiohttp.ClientSession, logger: logging.Logger) -> None:
        self._base_url = base_url
        self._session = session
        self._log = logger.getChild("evopt")

    async def optimize(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{self._base_url}/optimize/charge-schedule"
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        try:
            async with self._session.post(url, json=payload, headers=headers, timeout=60) as resp:
                resp.raise_for_status()
                data = await resp.json(loads=json.loads)
                self._log.debug("Received EVOpt response with keys: %s", list(data.keys()))
                return data
        except Exception as err:  # pragma: no cover - logged and re-raised
            self._log.error("Optimization request failed: %s", err)
            raise


class PayloadBuilder:
    """Converts EVCC state/forecasts into an EVOpt OptimizationInput payload."""

    def __init__(self, config: AppConfig, logger: logging.Logger) -> None:
        self._config = config
        self._log = logger.getChild("builder")
        try:
            self._tz = ZoneInfo(config.time_zone or DEFAULT_TIME_ZONE)
        except Exception:  # pragma: no cover - fallback
            self._log.warning("Invalid time zone '%s', falling back to %s", config.time_zone, DEFAULT_TIME_ZONE)
            self._tz = ZoneInfo(DEFAULT_TIME_ZONE)

    def build(self, state: Dict[str, Any]) -> Dict[str, Any]:
        forecast = state.get("forecast", {})
        horizon_steps = int(self._config.optimization_horizon_hours * 3600 / self._config.time_frame_seconds)
        horizon_steps = max(horizon_steps, 1)

        now = datetime.now(self._tz)
        time_points = self._generate_time_points(now, self._config.time_frame_seconds, horizon_steps)

        grid_series = self._extract_rate_series(forecast.get("grid", []), time_points)
        feedin_series = self._extract_rate_series(forecast.get("feedin", []), time_points)
        solar_series = self._extract_solar_series(forecast.get("solar", {}), time_points)

        home_power = float(state.get("homePower", 0))
        load_series = [max(home_power, 0.0) * self._config.time_frame_seconds / 3600.0 for _ in time_points]

        battery_info = self._extract_battery_details(state)

        payload = {
            "strategy": {
                "charging_strategy": "charge_before_export",
                "discharging_strategy": "discharge_before_import",
            },
            "grid": {
                "p_max_imp": self._config.grid_power_limit_w,
                "p_max_exp": self._config.grid_power_limit_w,
                "prc_p_imp_exc": 0,
            },
            "batteries": [
                {
                    "device_id": battery_info.device_id,
                    "charge_from_grid": self._config.battery.charge_from_grid,
                    "discharge_to_grid": self._config.battery.discharge_to_grid,
                    "s_min": battery_info.s_min,
                    "s_max": battery_info.s_max,
                    "s_initial": battery_info.s_initial,
                    "p_demand": [0.0] * horizon_steps,
                    "s_goal": [battery_info.s_goal] * horizon_steps,
                    "c_min": 0.0,
                    "c_max": self._config.battery.max_charge_power_w,
                    "d_max": self._config.battery.max_discharge_power_w,
                    "p_a": 0.0,
                }
            ],
            "time_series": {
                "dt": [self._config.time_frame_seconds] * horizon_steps,
                "gt": load_series,
                "ft": solar_series,
                "p_N": [max(v, 0.0) / 1000.0 for v in grid_series],
                "p_E": [max(v, 0.0) / 1000.0 for v in feedin_series],
            },
            "eta_c": 0.95,
            "eta_d": 0.95,
        }

        self._log.debug(
            "Built payload with %d steps (grid=%s, solar=%s)",
            horizon_steps,
            len(grid_series),
            len(solar_series),
        )
        return payload

    def _generate_time_points(self, start: datetime, step_seconds: int, steps: int) -> List[datetime]:
        start_seconds = (
            start.hour * 3600
            + start.minute * 60
            + start.second
            + start.microsecond / 1_000_000
        )
        aligned_seconds = start_seconds - (start_seconds % step_seconds)
        aligned_start = start.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(seconds=aligned_seconds)
        return [aligned_start + timedelta(seconds=step_seconds * idx) for idx in range(steps)]

    def _extract_rate_series(self, rates: List[Dict[str, Any]], time_points: List[datetime]) -> List[float]:
        if not rates:
            return [0.0] * len(time_points)

        parsed = []
        for entry in rates:
            try:
                start = date_parser.isoparse(entry["start"]).astimezone(self._tz)
                end = date_parser.isoparse(entry["end"]).astimezone(self._tz)
                value = float(entry.get("value", 0))
                parsed.append((start, end, value))
            except Exception:  # pragma: no cover - skip invalid rows
                continue

        parsed.sort(key=lambda item: item[0])
        values: List[float] = []
        idx = 0
        for instant in time_points:
            while idx + 1 < len(parsed) and instant >= parsed[idx + 1][0]:
                idx += 1
            selected = parsed[min(idx, len(parsed) - 1)][2]
            values.append(selected)
        return values

    def _extract_solar_series(self, solar: Dict[str, Any], time_points: List[datetime]) -> List[float]:
        timeseries = solar.get("timeseries") if isinstance(solar, dict) else None
        if not timeseries:
            return [0.0] * len(time_points)

        parsed = []
        for entry in timeseries:
            try:
                ts = date_parser.isoparse(entry["ts"]).astimezone(self._tz)
                val = float(entry.get("val", 0.0))
                parsed.append((ts, val))
            except Exception:  # pragma: no cover - skip invalid rows
                continue

        parsed.sort(key=lambda item: item[0])
        values: List[float] = []
        idx = 0
        for instant in time_points:
            while idx + 1 < len(parsed) and instant >= parsed[idx + 1][0]:
                idx += 1
            power_w = parsed[min(idx, len(parsed) - 1)][1]
            energy_wh = max(power_w, 0.0) * self._config.time_frame_seconds / 3600.0
            values.append(energy_wh)
        return values

    def _extract_battery_details(self, state: Dict[str, Any]) -> BatteryDetails:
        batteries = state.get("battery")
        if isinstance(batteries, list) and batteries:
            battery = batteries[0]
            capacity_kwh = float(battery.get("capacity", 0))
            soc_percent = float(battery.get("soc", 0))
        else:
            capacity_kwh = 0.0
            soc_percent = 0.0

        capacity_wh = max(capacity_kwh, 0.0) * 1000.0
        min_soc = max(self._config.battery.min_soc_percent, 0.0) / 100.0
        max_soc = min(self._config.battery.max_soc_percent, 100.0) / 100.0
        min_soc = min(min_soc, max_soc)
        initial_soc = max(min(soc_percent / 100.0, max_soc), min_soc)

        return BatteryDetails(
            device_id="battery_1",
            capacity_wh=capacity_wh,
            s_min=capacity_wh * min_soc,
            s_max=capacity_wh * max_soc if capacity_wh > 0 else capacity_wh,
            s_initial=capacity_wh * initial_soc,
            s_goal=capacity_wh * max_soc if capacity_wh > 0 else capacity_wh,
        )


class RestServer:
    """REST server exposing scheduler state."""

    def __init__(self, app_state: "SchedulerState", logger: logging.Logger) -> None:
        self._app_state = app_state
        self._log = logger.getChild("api")
        self._runner: Optional[web.AppRunner] = None
        self._site: Optional[web.TCPSite] = None

    async def start(self) -> None:
        app = web.Application()
        app.add_routes(
            [
                web.get("/api/status", self._handle_status),
                web.get("/api/metrics", self._handle_metrics),
                web.get("/api/optimization/request", self._handle_request),
                web.get("/api/optimization/response", self._handle_response),
                web.post("/api/optimization/run", self._handle_run_now),
            ]
        )
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, host="0.0.0.0", port=APP_PORT)
        await site.start()
        self._runner = runner
        self._site = site
        self._log.info("REST API listening on port %d", APP_PORT)

    async def stop(self) -> None:
        if self._site:
            await self._site.stop()
        if self._runner:
            await self._runner.cleanup()

    async def _handle_status(self, request: web.Request) -> web.Response:
        return web.json_response(self._app_state.status_snapshot())

    async def _handle_metrics(self, request: web.Request) -> web.Response:
        return web.json_response(self._app_state.metrics_snapshot())

    async def _handle_request(self, request: web.Request) -> web.Response:
        return web.json_response(self._app_state.optimization.payload or {})

    async def _handle_response(self, request: web.Request) -> web.Response:
        return web.json_response(self._app_state.optimization.response or {})

    async def _handle_run_now(self, request: web.Request) -> web.Response:
        self._log.info("Manual optimization requested")
        self._app_state.trigger_run()
        return web.json_response({"status": "scheduled"})


class SchedulerState:
    """Holds mutable runtime state shared across tasks."""

    def __init__(self) -> None:
        self.optimization = OptimizationSnapshot()
        self.last_evcc_poll: Optional[datetime] = None
        self.last_evcc_state: Optional[Dict[str, Any]] = None
        self.last_poll_error: Optional[str] = None
        self._run_now_event = asyncio.Event()

    def trigger_run(self) -> None:
        self._run_now_event.set()

    async def wait_for_run_trigger(self, timeout: Optional[float]) -> None:
        try:
            await asyncio.wait_for(self._run_now_event.wait(), timeout=timeout)
        except asyncio.TimeoutError:
            return
        finally:
            self._run_now_event.clear()

    def status_snapshot(self) -> Dict[str, Any]:
        return {
            "last_evcc_poll": self.last_evcc_poll.isoformat() if self.last_evcc_poll else None,
            "last_poll_error": self.last_poll_error,
            "last_optimization": self.optimization.as_dict(),
        }

    def metrics_snapshot(self) -> Dict[str, Any]:
        return {
            "evcc_state": self.last_evcc_state or {},
            "optimization": self.optimization.as_dict(),
        }


class SchedulerApplication:
    """Main orchestrator managing polling, optimization, and REST API."""

    def __init__(self, config: AppConfig) -> None:
        self._config = config
        self._setup_logging(config.log_level)
        self._log = logging.getLogger("scheduler")
        try:
            self._tz = ZoneInfo(config.time_zone or DEFAULT_TIME_ZONE)
        except Exception:
            self._log.warning("Invalid time zone '%s', using %s", config.time_zone, DEFAULT_TIME_ZONE)
            self._tz = ZoneInfo(DEFAULT_TIME_ZONE)
        self._state = SchedulerState()
        self._session = aiohttp.ClientSession()
        self._evcc = EvccClient(config.evcc_url, self._session, self._log)
        self._evopt = EvoptClient(config.evopt_url, self._session, self._log)
        self._builder = PayloadBuilder(config, self._log)
        self._rest = RestServer(self._state, self._log)
        self._tasks: List[asyncio.Task] = []

    def _setup_logging(self, level: str) -> None:
        logging.basicConfig(
            level=getattr(logging, level.upper(), logging.INFO),
            format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        )

    async def run(self) -> None:
        SHARE_DIR.mkdir(parents=True, exist_ok=True)
        await self._rest.start()
        self._tasks = [
            asyncio.create_task(self._poll_loop(), name="evcc-poll"),
            asyncio.create_task(self._optimization_loop(), name="evopt-run"),
        ]
        self._log.info("Scheduler started")
        await asyncio.gather(*self._tasks)

    async def shutdown(self) -> None:
        for task in self._tasks:
            task.cancel()
        await asyncio.gather(*self._tasks, return_exceptions=True)
        await self._rest.stop()
        await self._session.close()
        self._log.info("Scheduler stopped")

    async def _poll_loop(self) -> None:
        interval = max(self._config.evcc_poll_interval_seconds, 5)
        while True:
            try:
                state = await self._evcc.fetch_state()
                self._state.last_evcc_state = state
                self._state.last_evcc_poll = datetime.now(tz=self._tz)
                self._state.last_poll_error = None
            except Exception as err:  # pragma: no cover - logged already
                self._state.last_poll_error = str(err)
                self._log.warning("EVCC polling failed: %s", err)
            await asyncio.sleep(interval)

    async def _optimization_loop(self) -> None:
        interval = max(self._config.scheduler_interval_seconds, 60)
        while True:
            await self._state.wait_for_run_trigger(timeout=interval)
            if not self._state.last_evcc_state:
                self._log.warning("Skipping optimization: no EVCC data yet")
                continue
            await self._execute_optimization(self._state.last_evcc_state)

    async def _execute_optimization(self, evcc_state: Dict[str, Any]) -> None:
        self._state.optimization = OptimizationSnapshot(requested_at=datetime.now(tz=self._tz))
        try:
            payload = self._builder.build(evcc_state)
            self._state.optimization.payload = payload
            self._write_json(payload, SHARE_DIR / "last_request.json")
            response = await self._evopt.optimize(payload)
            self._state.optimization.response = response
            self._write_json(response, SHARE_DIR / "last_response.json")
            self._state.optimization.completed_at = datetime.now(tz=self._tz)
            self._state.optimization.error = None
            self._log.info("Optimization run completed successfully")
        except Exception as err:  # pragma: no cover - logged already
            self._state.optimization.error = str(err)
            self._state.optimization.completed_at = datetime.now(tz=self._tz)
            self._log.error("Optimization run failed: %s", err)

    def _write_json(self, data: Dict[str, Any], path: Path) -> None:
        try:
            path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        except Exception as err:  # pragma: no cover - log but do not fail
            self._log.debug("Failed to write %s: %s", path, err)


async def async_main() -> None:
    config = AppConfig.load()
    app = SchedulerApplication(config)
    try:
        await app.run()
    except asyncio.CancelledError:  # pragma: no cover
        pass
    finally:
        await app.shutdown()


def main() -> None:
    try:
        asyncio.run(async_main())
    except KeyboardInterrupt:  # pragma: no cover
        pass


if __name__ == "__main__":
    main()
