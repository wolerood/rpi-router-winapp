import os


DEFAULT_API_URL = os.environ.get(
    "RPI_ROUTER_API_URL",
    "http://rpi-router.local:8080",
)
DEFAULT_API_TOKEN = os.environ.get("RPI_ROUTER_API_TOKEN", "")
REQUEST_TIMEOUT = 3
