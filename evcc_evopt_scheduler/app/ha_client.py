"""Home Assistant service client for the EVCC EVOpt Scheduler add-on."""
from __future__ import annotations

import logging
from typing import Any, Dict

import aiohttp


class HomeAssistantServiceClient:
    """Client used to call Home Assistant services via the REST API."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        base_url: str,
        token: str,
        verify_ssl: bool,
        logger: logging.Logger,
    ) -> None:
        self._session = session
        self._base_url = base_url.rstrip("/")
        self._headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        self._ssl = verify_ssl
        self._log = logger.getChild("ha")

    async def call_service(self, service: str, data: Dict[str, Any]) -> None:
        """Call a Home Assistant service."""
        if "." not in service:
            raise ValueError(f"Service '{service}' must be in 'domain.service' format")
        domain, service_name = service.split(".", 1)
        url = f"{self._base_url}/services/{domain}/{service_name}"

        self._log.debug("Calling HA service %s with data %s", service, data)
        async with self._session.post(url, headers=self._headers, json=data, ssl=self._ssl) as response:
            if response.status >= 400:
                text = await response.text()
                self._log.error(
                    "Home Assistant service %s failed (%s): %s", service, response.status, text
                )
                response.raise_for_status()
