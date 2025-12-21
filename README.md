# Home Assistant Integration: EVOpt - EV Charging Optimization

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)

A Home Assistant integration for EVOpt, an EV charging optimization system that provides intelligent charging schedules based on energy prices, solar production, and battery storage.

## Features

- **Real-time Monitoring**: Monitor EVOpt service health and status
- **Optimization Results**: Access charging optimization data and schedules
- **Battery Management**: Track battery charging/discharging patterns
- **Grid Interaction**: Monitor grid import/export and energy flows

## Requirements

- A running EVOpt instance (https://github.com/andig/evopt)
- Home Assistant 2024.1.0 or later
- HACS (for easy installation)

## Installation

### Option 1: HACS (Recommended)

1. Add this repository as a custom repository in HACS
2. Search for "EVOpt" and install the integration
3. Restart Home Assistant

### Option 2: Manual Installation

1. Copy the `custom_components/evopt` folder to your Home Assistant `custom_components` directory
2. Restart Home Assistant

## Configuration

1. Go to **Settings** → **Devices & Services** → **Add Integration**
2. Search for "EVOpt" and select it
3. Enter your EVOpt server URL (e.g., `http://your-evopt-server:7050`)
4. Complete the setup

## Available Sensors

- **EVOpt Status**: Service health and connection status
- **Optimization Status**: Current optimization state (Optimal/Infeasible/etc.)
- **Objective Value**: Economic benefit from optimization (€)
- **Battery Count**: Number of batteries in the system
- **Grid Import Total**: Total energy imported from grid (Wh)
- **Grid Export Total**: Total energy exported to grid (Wh)

## Services

### Run Optimization

You can manually trigger an optimization using the `evopt.run_optimization` service. This allows you to provide custom parameters for the optimization.

**Service Parameters:**
- `batteries`: Array of battery configurations
- `time_series`: Time series data (dt, gt, ft, p_N, p_E)
- `strategy`: Optimization strategy preferences
- `grid`: Grid configuration (p_max_imp, p_max_exp, prc_p_imp_exc)
- `eta_c`: Charging efficiency (default: 0.95)
- `eta_d`: Discharging efficiency (default: 0.95)

## API Integration

This integration communicates with EVOpt's REST API endpoints:

- `/optimize/health` - Service health check
- `/optimize/charge-schedule` - Charging optimization requests

The integration supports the full EVOpt API specification including:
- Battery configurations with charging/discharging constraints
- Time series data for energy forecasts and grid prices
- Optimization strategies and grid power limits
- Detailed optimization results with power flows and state of charge data

## API Integration

This integration communicates with EVOpt's REST API endpoints:

- `/optimize/health` - Service health check
- `/optimize/charge-schedule` - Charging optimization requests

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Issues

If you encounter any issues, please report them on the [GitHub Issues](https://github.com/your-username/ha-evopt/issues) page.

## License

This project is licensed under the MIT License - see the LICENSE file for details.