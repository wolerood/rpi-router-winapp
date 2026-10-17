import requests


class ApiError(Exception):
    pass


class ApiClient:
    WRITE_METHODS = {"POST", "PATCH", "DELETE"}

    def __init__(self, base_url: str, timeout: int = 3, api_token: str = ""):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.api_token = api_token.strip()
        self.session = requests.Session()
        # This client talks directly to the router. System proxy settings can
        # turn local .local requests into misleading 502 responses.
        self.session.trust_env = False

    def set_base_url(self, base_url: str):
        self.base_url = base_url.rstrip("/")

    def set_api_token(self, api_token: str):
        self.api_token = api_token.strip()

    def _request(self, method: str, path: str, **kwargs):
        url = f"{self.base_url}{path}"
        method = method.upper()

        if method in self.WRITE_METHODS:
            headers = dict(kwargs.pop("headers", {}))
            if self.api_token:
                headers["X-API-Token"] = self.api_token
            kwargs["headers"] = headers

        try:
            response = self.session.request(
                method,
                url,
                timeout=self.timeout,
                **kwargs,
            )
        except requests.RequestException as exc:
            raise ApiError(
                f"Ошибка соединения с API ({method} {url}): {exc}"
            ) from exc

        try:
            data = response.json()
        except ValueError:
            data = None

        if not response.ok:
            if isinstance(data, dict) and "error" in data:
                message = data["error"]
            else:
                message = f"HTTP {response.status_code}: {method} {url}"

            raise ApiError(message)

        return data

    def get_users(self):
        return self._request("GET", "/users")

    def create_user(self, name: str):
        return self._request(
            "POST",
            "/users",
            json={"name": name},
        )

    def rename_user(self, user_id: int, name: str):
        return self._request(
            "PATCH",
            f"/users/{user_id}",
            json={"name": name},
        )

    def set_access_mode(self, user_id: int, access_mode: str):
        return self._request(
            "PATCH",
            f"/users/{user_id}/access_mode",
            json={"access_mode": access_mode},
        )

    def delete_user(self, user_id: int):
        return self._request(
            "DELETE",
            f"/users/{user_id}",
        )

    def get_user_access(self, user_id: int):
        return self._request("GET", f"/access/{user_id}")

    def get_devices(self):
        return self._request("GET", "/devices")

    def create_device(self, user_id: int, mac: str, name: str):
        return self._request(
            "POST",
            "/devices",
            json={
                "user_id": user_id,
                "mac": mac,
                "name": name,
            },
        )

    def update_device(self, device_id: int, **fields):
        payload = {
            key: value
            for key, value in fields.items()
            if key in {"name", "user_id"}
        }

        return self._request(
            "PATCH",
            f"/devices/{device_id}",
            json=payload,
        )

    def delete_device(self, device_id: int):
        return self._request(
            "DELETE",
            f"/devices/{device_id}",
        )

    def get_clients(self):
        return self._request("GET", "/clients")

    def get_schedules(self):
        return self._request("GET", "/schedules")

    def create_schedule(
        self,
        user_id: int,
        weekday: int,
        start: str,
        end: str,
    ):
        return self._request(
            "POST",
            "/schedules",
            json={
                "user_id": user_id,
                "weekday": weekday,
                "start": start,
                "end": end,
            },
        )

    def update_schedule(self, schedule_id: int, **fields):
        payload = {
            key: value
            for key, value in fields.items()
            if key in {"user_id", "weekday", "start", "end"}
        }

        return self._request(
            "PATCH",
            f"/schedules/{schedule_id}",
            json=payload,
        )

    def delete_schedule(self, schedule_id: int):
        return self._request(
            "DELETE",
            f"/schedules/{schedule_id}",
        )

    def get_logs(self):
        return self._request("GET", "/logs")
