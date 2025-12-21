# EVCC EVOpt Scheduler

This repository contains a Home Assistant add-on named **EVCC EVOpt Scheduler**.
The add-on polls an EVCC instance for current site metrics and forecast data,
translates the information into EVOpt's optimization input format, and executes
regular optimization runs. The latest optimization inputs and results are
exposed through a lightweight REST API.

The repository follows the standard Home Assistant add-on layout:

```
evcc-evopt-scheduler/
├── app/                 # Python sources
├── config.yaml          # Add-on metadata and option schema
├── Dockerfile           # Container build recipe
├── README.md            # Add-on specific documentation
├── requirements.txt     # Python dependencies
├── rootfs/              # s6-overlay service and init scripts
└── build.yaml           # Architecture build targets
```

## Add-on Overview

- **EVCC Polling**: Retrieves `/api/state` from EVCC to obtain live power
  readings, battery state, and forecast data (grid tariffs, feed-in, solar
  production).
- **EVOpt Execution**: Builds an `OptimizationInput` payload using configurable
  battery constraints and runs the EVOpt REST endpoint on a fixed cadence.
- **REST API**: Serves status, metrics, and the last optimization
  request/response over a configurable HTTP port (default `7060`).

Refer to `evcc-evopt-scheduler/README.md` for installation instructions,
configuration details, and the API surface provided by the add-on.
