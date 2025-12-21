# EVCC EVOpt Scheduler Add-on

This Home Assistant add-on polls data from EVCC and forwards forecasts to EVOpt to
calculate optimized battery usage schedules. It exposes a small REST API that your
Home Assistant configuration (or other tools) can poll to access the generated
optimization requests and responses.

## Features

- Poll EVCC `/api/state` for live site metrics and forecasts
- Translate EVCC forecasts into EVOpt `OptimizationInput` payloads
- Run EVOpt optimizations on a configurable cadence
- Store the latest EVOpt request/response for troubleshooting
- Expose REST endpoints for status, metrics, and on-demand optimization runs
- Configurable battery constraints (charge/discharge limits, SoC bounds)

## Configuration Options

All options are available via the add-on UI. Defaults assume that both EVCC and
EVOpt run as Home Assistant add-ons using their standard internal hostnames.

| Option | Description | Default |
| --- | --- | --- |
| `evcc_url` | Base URL of the EVCC API | `http://core-evcc:7070` |
| `evopt_url` | Base URL of the EVOpt API | `http://core-evopt:7050` |
| `time_zone` | IANA time zone used for forecast alignment | `Europe/Berlin` |
| `time_frame_seconds` | Resolution of the optimization (e.g. 900 for 15 min) | `900` |
| `optimization_horizon_hours` | Optimization horizon | `48` |
| `evcc_poll_interval_seconds` | How often to refresh EVCC state | `15` |
| `scheduler_interval_seconds` | How often to run EVOpt | `900` |
| `grid_power_limit_w` | Grid import/export limit in watts | `11000` |
| `api_port` | Port exposing the add-on REST API | `7060` |
| `log_level` | Log verbosity (`DEBUG`, `INFO`, `WARNING`, `ERROR`) | `INFO` |
| `battery.*` | Battery constraint settings passed to EVOpt | see config |

## REST API

| Endpoint | Method | Description |
| --- | --- | --- |
| `/api/status` | GET | High-level health information |
| `/api/metrics` | GET | Last EVCC snapshot and scheduler stats |
| `/api/optimization/request` | GET | Most recent EVOpt payload |
| `/api/optimization/response` | GET | Most recent EVOpt response |
| `/api/optimization/run` | POST | Trigger an on-demand optimization |

All endpoints return JSON. The service listens on port `8000` inside the add-on
container. Home Assistant can reach it through the supervisor proxy using
`http://[HOST]:[PORT]` once you expose the add-on locally (e.g. via Ingress proxy
or a command-line sensor).

## Logs & Debugging

The add-on writes structured logs via the Supervisor log window. Setting the
`log_level` option to `DEBUG` enables verbose tracing of EVCC responses and EVOpt
payload generation.

Recent EVOpt request/response bodies are persisted in `/share/evcc-evopt-scheduler`
for inspection and to assist in debugging forecast alignment issues.

## Roadmap

- Home Assistant sensor platform consuming the REST API automatically
- Support for multiple batteries and fine-grained load forecasts
- Optional MQTT publisher for multi-system integration

Contributions and feedback are welcome! Open an issue or PR in
[`stefanriegel/evcc-evopt-scheduler`](https://github.com/stefanriegel/evcc-evopt-scheduler).
