"""Constants for EVOpt integration."""
DOMAIN = "evopt"
NAME = "EVOpt - EV Charging Optimization"
NAME_SHORT = "EVOpt"

PLATFORMS = ["sensor"]

SERVICE_RUN_OPTIMIZATION = "run_optimization"

STARTUP_MESSAGE = f"""
-------------------------------------------------------------------
{NAME}
-------------------------------------------------------------------
This is a custom integration!
If you have any issues with this you need to open an issue here:
https://github.com/your-username/ha-evopt
-------------------------------------------------------------------
"""