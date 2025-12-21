# EVCC EVOpt Scheduler Add-on Documentation

This Home Assistant add-on bridges EVCC and EVOpt to generate optimized battery charging schedules based on solar forecasts, grid prices, and battery state.

## Overview

The add-on continuously polls EVCC for site data (battery state, solar forecast, grid prices), translates this into EVOpt optimization requests, and applies the resulting schedules. It can optionally control batteries directly through Home Assistant service calls.

## How It Works

1. **EVCC Polling**: Every `evcc_poll_interval_seconds`, the add-on fetches the current state from EVCC's `/api/state` endpoint
2. **Optimization**: Every `scheduler_interval_seconds`, it sends the current forecast to EVOpt's `/optimize/charge-schedule` endpoint
3. **Battery Control**: If configured, it immediately calls Home Assistant services to apply the optimization results
4. **Persistence**: Request/response JSON files are saved to `/share/evcc-evopt-scheduler/` for debugging

## Configuration

### EVCC Integration

| Option | Description | Default |
|--------|-------------|---------|
| `evcc_url` | Base URL of your EVCC instance | `http://core-evcc:7070` |
| `evcc_poll_interval_seconds` | How often to refresh EVCC state | `15` |

The add-on expects EVCC to provide:
- Battery information (`battery[]` array with power, capacity, soc)
- Solar and grid price forecasts (`forecast` object)
- Pre-built optimization request template (`evopt.req`)

### EVOpt Integration

| Option | Description | Default |
|--------|-------------|---------|
| `evopt_url` | Base URL of your EVOpt instance | `http://core-evopt:7050` |
| `scheduler_interval_seconds` | How often to run optimization | `900` (15 minutes) |
| `optimization_horizon_hours` | Forecast horizon | `48` |
| `time_frame_seconds` | Time resolution (slot duration) | `900` (15 minutes) |

### Time and Grid Settings

| Option | Description | Default |
|--------|-------------|---------|
| `time_zone` | IANA timezone (e.g. `Europe/Berlin`) | `Europe/Berlin` |
| `grid_power_limit_w` | Maximum grid import/export power | `11000` |

### Battery Constraints

These options define the battery's physical limits sent to EVOpt:

| Option | Description | Default |
|--------|-------------|---------|
| `battery.charge_from_grid` | Allow charging from grid | `true` |
| `battery.discharge_to_grid` | Allow discharging to grid | `true` |
| `battery.min_soc_percent` | Minimum state of charge | `5` |
| `battery.max_soc_percent` | Maximum state of charge | `95` |
| `battery.max_charge_power_w` | Maximum charge power | `10000` |
| `battery.max_discharge_power_w` | Maximum discharge power | `10000` |

### Home Assistant API Access

To enable battery control, provide a long-lived access token:

| Option | Description | Default |
|--------|-------------|---------|
| `ha_api_url` | Home Assistant API URL | `http://supervisor/core/api` |
| `ha_token` | Long-lived access token | _(empty)_ |
| `ha_verify_ssl` | Verify SSL certificates | `false` |

**How to create a long-lived access token:**
1. Go to your Home Assistant profile page
2. Scroll to "Long-Lived Access Tokens"
3. Click "Create Token"
4. Give it a name (e.g., "EVCC EVOpt Scheduler")
5. Copy the token and paste it into the `ha_token` field

### Battery Control Profiles

Configure one or more batteries to control:

```yaml
batteries:
  - name: "Main Battery"
    strategy: grid_balancing
    result_index: 0
    min_soc_percent: 10
    max_soc_percent: 90
    ha_service: mqtt.publish
    ha_service_data:
      topic: "battery/command"
      payload: '{"mode": "{mode}", "power": {target_power}}'
    context:
      custom_field: "value"
```

#### Battery Profile Options

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Human-readable battery name |
| `strategy` | enum | Yes | Control strategy: `grid_balancing`, `fixed_discharge`, `fixed_charge` |
| `result_index` | int | No | Index in EVOpt response (default: 0) |
| `min_soc_percent` | int | No | Override global min SoC (default: from `battery.min_soc_percent`) |
| `max_soc_percent` | int | No | Override global max SoC (default: from `battery.max_soc_percent`) |
| `ha_service` | string | Yes | Home Assistant service to call (e.g., `mqtt.publish`, `select.select_option`) |
| `ha_service_data` | dict | No | Service call data with context variable substitution |
| `context` | dict | No | Additional context variables |

#### Control Strategies

**`grid_balancing`** (Recommended)
- Follows EVOpt's charge/discharge recommendations
- Respects min/max SoC bounds
- Sets `mode` to `charge`, `discharge`, or `idle`
- Provides `charge_power` and `discharge_power` from EVOpt response

**`fixed_discharge`**
- Always discharge at maximum power when SoC > min threshold
- Ignores EVOpt recommendations
- Useful for simple export strategies

**`fixed_charge`**
- Always charge at maximum power when SoC < max threshold
- Ignores EVOpt recommendations
- Useful for simple import strategies

#### Context Variables

The following variables are available in `ha_service_data` for string substitution:

| Variable | Type | Description | Example |
|----------|------|-------------|---------|
| `{mode}` | string | `charge`, `discharge`, or `idle` | `charge` |
| `{target_power}` | int | Absolute power value (W) | `5000` |
| `{charge_power}` | int | Charging power from EVOpt (W, 0 if discharging) | `5000` |
| `{discharge_power}` | int | Discharging power from EVOpt (W, 0 if charging) | `0` |
| `{soc}` | float | State of charge (%) | `45.5` |

**Example substitution:**
```yaml
ha_service_data:
  topic: "victron/command"
  payload: "{mode}:{target_power}"
# Becomes: {"topic": "victron/command", "payload": "charge:5000"}
```

### REST API

The add-on exposes a REST API on port `7060` (configurable via `api_port`):

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/status` | GET | Returns `{"status": "ok", "service": "evcc-evopt-scheduler"}` |
| `/api/metrics` | GET | Returns last EVCC state and scheduler statistics |
| `/api/optimization/request` | GET | Returns the last EVOpt request payload |
| `/api/optimization/response` | GET | Returns the last EVOpt response |
| `/api/optimization/run` | POST | Triggers an immediate optimization run |

Access the API from Home Assistant using:
```
http://[addon-host]:7060/api/status
```

### Logging

| Option | Description | Default |
|--------|-------------|---------|
| `log_level` | Log verbosity | `INFO` |

Available levels:
- `DEBUG`: Verbose logging including full EVCC state, EVOpt requests/responses
- `INFO`: Standard operational logging
- `WARNING`: Only warnings and errors
- `ERROR`: Only errors

## Battery Control Examples

### Example 1: Victron via MQTT

```yaml
batteries:
  - name: "Victron MultiPlus"
    strategy: grid_balancing
    ha_service: mqtt.publish
    ha_service_data:
      topic: "victron/battery/command"
      payload: '{"mode": "{mode}", "power": {target_power}}'
```

### Example 2: Huawei via Integration

```yaml
batteries:
  - name: "Huawei LUNA2000"
    strategy: grid_balancing
    ha_service: select.select_option
    ha_service_data:
      entity_id: select.huawei_battery_mode
      option: "{mode}"
```

### Example 3: Multiple Batteries

```yaml
batteries:
  - name: "Battery 1"
    strategy: grid_balancing
    result_index: 0
    ha_service: mqtt.publish
    ha_service_data:
      topic: "battery1/command"
      payload: "{mode}:{target_power}"
  
  - name: "Battery 2"
    strategy: grid_balancing
    result_index: 1
    ha_service: mqtt.publish
    ha_service_data:
      topic: "battery2/command"
      payload: "{mode}:{target_power}"
```

### Example 4: Using a Home Assistant Script

```yaml
batteries:
  - name: "My Battery"
    strategy: grid_balancing
    ha_service: script.control_battery
    ha_service_data:
      mode: "{mode}"
      power: "{target_power}"
```

Then in Home Assistant create a script:
```yaml
# configuration.yaml or scripts.yaml
script:
  control_battery:
    sequence:
      - service: mqtt.publish
        data:
          topic: "battery/set"
          payload: >
            {{ mode }}:{{ power }}
```

## Debugging

### Check Add-on Logs

1. Go to Settings → Add-ons → EVCC EVOpt Scheduler
2. Click the "Log" tab
3. Set `log_level: DEBUG` in configuration for verbose output

### Check Persisted Files

The add-on writes the following files to `/share/evcc-evopt-scheduler/`:

- `last_evcc_state.json` - Most recent EVCC state
- `last_request.json` - Most recent EVOpt request
- `last_response.json` - Most recent EVOpt response

Access these via:
- Samba share: `\\homeassistant\share\evcc-evopt-scheduler\`
- SSH: `/share/evcc-evopt-scheduler/`
- File Editor add-on

### Common Issues

**Add-on won't start:**
- Check that EVCC and EVOpt are running and accessible
- Verify URLs in configuration
- Check add-on logs for connection errors

**Battery control not working:**
- Verify `ha_token` is set correctly
- Check Home Assistant logs for service call errors
- Test the service manually from Developer Tools → Services
- Verify service name and entity IDs are correct

**Optimization not running:**
- Check that EVCC provides valid forecast data
- Verify EVOpt is responding correctly
- Review debug logs with `log_level: DEBUG`
- Check `/share/evcc-evopt-scheduler/last_request.json` for payload issues

## Support

For issues, questions, or contributions:
- GitHub: [stefanriegel/evcc-evopt-scheduler](https://github.com/stefanriegel/evcc-evopt-scheduler)
- Open an issue for bug reports or feature requests
- Pull requests are welcome!
