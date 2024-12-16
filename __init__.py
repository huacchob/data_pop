"""Initialize Job Repository."""

import typing as t

from nautobot.apps.jobs import register_jobs

from .jobs.location_creation import LocationCreation

jobs: list[t.Any] = [
    LocationCreation,
]

register_jobs(*jobs)
