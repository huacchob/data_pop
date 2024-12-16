"""Data population jobs."""

import typing as t

from location_creation import LocationCreation
from nautobot.apps.jobs import register_jobs

jobs: list[t.Any] = [
    LocationCreation,
]

register_jobs(*jobs)
