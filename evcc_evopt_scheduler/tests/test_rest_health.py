import logging
import unittest
from datetime import datetime, timezone

from aiohttp.test_utils import AioHTTPTestCase

from app.main import RestServer, SchedulerState


class RestHealthTests(AioHTTPTestCase):
    async def get_application(self):
        self.state = SchedulerState()
        self.server = RestServer(self.state, logging.getLogger("test"), 0)
        return self.server.build_application()

    async def test_health_response_is_exact_and_repeatable(self):
        first = await self.client.get("/api/health")
        first_body = await first.read()
        second = await self.client.get("/api/health")
        second_body = await second.read()

        self.assertEqual(first.status, 200)
        self.assertEqual(
            first.headers["Content-Type"], "application/json; charset=utf-8"
        )
        self.assertEqual(
            await first.json(),
            {"status": "ok", "service": "evcc-evopt-scheduler"},
        )
        self.assertEqual(first_body, second_body)

    async def test_health_response_does_not_expose_scheduler_state(self):
        baseline = await self.client.get("/api/health")
        baseline_body = await baseline.read()
        self.state.last_evcc_poll = datetime(2026, 8, 27, tzinfo=timezone.utc)
        self.state.last_poll_error = "sensitive dependency error"
        self.state.optimization.payload = {"secret": "request"}
        self.state.optimization.response = {"secret": "response"}

        response = await self.client.get("/api/health")
        response_body = await response.read()

        self.assertEqual(response.status, 200)
        self.assertEqual(response_body, baseline_body)
        self.assertEqual(
            await response.json(),
            {"status": "ok", "service": "evcc-evopt-scheduler"},
        )

    async def test_route_table_is_additive(self):
        routes = {
            (route.method, route.resource.canonical)
            for route in self.app.router.routes()
            if route.method != "HEAD"
        }

        self.assertEqual(
            routes,
            {
                ("GET", "/api/health"),
                ("GET", "/api/status"),
                ("GET", "/api/metrics"),
                ("GET", "/api/optimization/request"),
                ("GET", "/api/optimization/response"),
                ("POST", "/api/optimization/run"),
            },
        )

    async def test_status_response_shape_is_unchanged(self):
        response = await self.client.get("/api/status")

        self.assertEqual(response.status, 200)
        self.assertEqual(
            set((await response.json()).keys()),
            {"last_evcc_poll", "last_poll_error", "last_optimization"},
        )

    async def test_health_rejects_post(self):
        response = await self.client.post("/api/health")

        self.assertEqual(response.status, 405)


if __name__ == "__main__":
    unittest.main()
