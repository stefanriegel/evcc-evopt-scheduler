# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.17] - 2025-12-21

### Fixed
- Corrected port reference in README from 8000 to 7060

## [0.1.16] - 2025-12-21

### Fixed
- Renamed add-on directory to `evcc_evopt_scheduler` to match slug and fix visibility in Home Assistant add-on store

## [0.1.15] - 2025-12-21

### Fixed
- Simplified `batteries` schema to avoid Home Assistant Supervisor validation errors
- Changed from deeply nested object schema to simple list validation (HA Supervisor limitation)

## [0.1.14] - 2025-12-21

### Fixed
- Add missing `homeassistant_api: true` permission in config.yaml (required for HA API access)

## [0.1.13] - 2025-12-21

### Added
- DOCS.md with comprehensive add-on documentation
- CHANGELOG.md for version tracking
- icon.png (128x128) for add-on store display
- logo.png (1024x1024) for add-on branding
- Dockerfile labels for proper Home Assistant add-on identification

### Changed
- Aligned with Home Assistant add-on best practices
- Enhanced documentation structure

## [0.1.12] - 2025-12-21

### Added
- Battery control via Home Assistant service calls
- Three control strategies: `grid_balancing`, `fixed_discharge`, `fixed_charge`
- Context variable substitution in service payloads (`{mode}`, `{target_power}`, `{charge_power}`, `{discharge_power}`, `{soc}`)
- Per-battery configuration with individual HA service mappings
- `HomeAssistantServiceClient` for REST API service calls
- `BatteryController` with strategy pattern implementation
- New config options: `ha_api_url`, `ha_token`, `ha_verify_ssl`, `batteries[]`
- DOCS.md with comprehensive documentation
- CHANGELOG.md for version tracking

### Changed
- Updated README with battery control documentation
- Enhanced main scheduler to integrate battery control after optimization

## [0.1.11] - 2025-12-21

### Added
- Debug logging for EVCC state, EVOpt requests, and EVOpt responses
- Configurable REST API port via `api_port` option
- Persisted debug artifacts: `last_evcc_state.json`, `last_request.json`, `last_response.json`

### Changed
- Enhanced logging throughout the application
- Default API port set to 7060

## [0.1.10] - 2025-12-20

### Fixed
- Install app package under `/app/app` for proper module resolution
- Execute scheduler via absolute script path
- Mark cont-init script executable
- Export PYTHONPATH during cont-init phase

## [0.1.9] - 2025-12-20

### Changed
- Refactor to adopt s6-overlay service layout
- Use `#!/usr/bin/with-contenv bashio` for service scripts

## [0.1.8] - 2025-12-20

### Fixed
- Revert to module execution with validated workdir
- Run scheduler via main.py script
- Export PYTHONPATH for add-on entrypoint
- Ensure app package is on Python path

## [0.1.1] - 2025-12-19

### Added
- Build matrix for Home Assistant Supervisor base images
- Multi-architecture support (aarch64, amd64, armhf, armv7, i386)

## [0.1.0] - 2025-12-18

### Added
- Initial release of EVCC EVOpt Scheduler add-on
- EVCC state polling every 15 seconds
- EVOpt optimization runs every 15 minutes
- REST API with endpoints:
  - `/api/status` - Health check
  - `/api/metrics` - EVCC state and scheduler statistics
  - `/api/optimization/request` - Last EVOpt request payload
  - `/api/optimization/response` - Last EVOpt response
  - `/api/optimization/run` - Trigger on-demand optimization
- Configurable battery constraints (SoC limits, charge/discharge power)
- Time zone and scheduling configuration
- Grid power limit configuration
- Persistent storage in `/share/evcc-evopt-scheduler/`

[0.1.12]: https://github.com/stefanriegel/evcc-evopt-scheduler/compare/v0.1.11...v0.1.12
[0.1.11]: https://github.com/stefanriegel/evcc-evopt-scheduler/compare/v0.1.10...v0.1.11
[0.1.10]: https://github.com/stefanriegel/evcc-evopt-scheduler/compare/v0.1.9...v0.1.10
[0.1.9]: https://github.com/stefanriegel/evcc-evopt-scheduler/compare/v0.1.8...v0.1.9
[0.1.8]: https://github.com/stefanriegel/evcc-evopt-scheduler/compare/v0.1.1...v0.1.8
[0.1.1]: https://github.com/stefanriegel/evcc-evopt-scheduler/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/stefanriegel/evcc-evopt-scheduler/releases/tag/v0.1.0
