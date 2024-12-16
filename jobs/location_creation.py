"""Location creation job."""

import csv
import typing as t

from django.core.exceptions import ValidationError
from django.db.models.fields.files import FieldFile
from nautobot.apps.jobs import BooleanVar, FileVar, Job
from nautobot.dcim.models import Location, LocationType
from nautobot.extras.models import Status

from .state_abbreviations import STATE_ABBREVIATIONS

name: str = "Location Jobs"


class LocationCreation(Job):
    """Job to create locations.

    Args:
        Job (Job): Job class.
    """

    csv_file = FileVar(
        label="Locations CSV File",
        description="CSV file containing location data.",
        required=True,
    )
    debug = BooleanVar(
        label="Debug",
        description="Debug",
        required=False,
        default=False,
    )

    class Meta:
        """Meta class."""

        name: str = "Create Locations"

    def __init__(self, *args, **kwargs) -> None:
        """Initialize Job."""
        super().__init__(*args, **kwargs)
        self.csv_file: FieldFile
        self.debug: bool
        self.locations: t.List[t.Dict[str, str]]

    def find_state_abbr(self, state: str) -> t.Optional[str]:
        """Find the state based on the two letter code.

        Args:
            state (str): Name of state.

        Returns:
            t.Optional[str]: state if found.
        """
        if len(state) == 2:
            state_name: str | None = STATE_ABBREVIATIONS.get(state.upper())
            if state_name:
                return state_name
            else:
                self.logger.error(msg="State not recognized.")
                raise ValidationError(message="State not recognized.")
        else:
            return state

    def get_location_type(
        self,
        site_name: t.Optional[str] = None,
        type_name: t.Optional[str] = None,
    ) -> t.Optional[LocationType]:
        """Get location type.

        Args:
            site_name (str): site name.

        Returns:
            LocationType | None: locationType if found.
        """
        location_type: t.Optional[LocationType] = None

        try:
            if site_name:
                if site_name.endswith("-DC"):
                    location_type = LocationType.objects.get(
                        name="Data Center",
                    )
                elif site_name.endswith("-BR"):
                    location_type = LocationType.objects.get(name="Branch")

                return location_type

            elif type_name:
                location_type = LocationType.objects.get(name=type_name)
                return location_type

            else:
                self.logger.error(msg="Location type not passed.")

        except LocationType.DoesNotExist:
            self.logger.error(
                msg="Location type for {site_name} not found".format(
                    site_name=site_name,
                )
            )

    def parse_csv(self) -> None:
        """Parse CSV file."""
        try:
            csv_data: bytes = self.csv_file.read()
            self.locations = list(
                csv.DictReader(
                    f=csv_data.decode(encoding="utf-8").splitlines(),
                )
            )
        except csv.Error as e:
            raise ValidationError(
                message=f"Error occurred while parsing CSV file: {e}",
            ) from e

    def create_locations(self) -> None:
        """Create locations."""
        state_location_type: LocationType | None = self.get_location_type(
            type_name="State",
        )
        city_location_type: LocationType | None = self.get_location_type(
            type_name="City",
        )
        active_status_object: Status = Status.objects.get(name="Active")
        for row in self.locations:
            state: str | None = self.find_state_abbr(
                state=row["state"],
            )

            state_object, state_created = Location.objects.get_or_create(
                name=state,
                defaults={
                    "name": state,
                    "status": active_status_object,
                    "location_type": state_location_type,
                },
            )
            if state_created and self.debug:
                self.logger.info(
                    msg=f"Created the Following Entry - State: {state}",
                )

            city, city_created = Location.objects.get_or_create(
                name=row["city"],
                defaults={
                    "name": row["city"],
                    "status": active_status_object,
                    "parent": state_object,
                    "location_type": city_location_type,
                },
            )
            if city_created and self.debug:
                self.logger.info(
                    msg=f"Created the Following Entry - City: {city.name}",
                )

            location_type: LocationType | None = self.get_location_type(
                site_name=row["name"]
            )
            site, location_created = Location.objects.get_or_create(
                name=row["name"],
                defaults={
                    "name": row["name"],
                    "status": active_status_object,
                    "location_type": location_type,
                    "parent": city,
                },
            )
            if location_created and self.debug:
                self.logger.info(
                    msg="Created the Following Entry - Site: {site}".format(
                        site=site.name,
                    )
                )
            if not location_created and self.debug:
                self.logger.info(msg="Location already exists")

    def run(self, **data: t.Any) -> None:
        """Run the job."""
        self.csv_file = data["csv_file"]
        self.debug = data["debug"]
        self.parse_csv()
        self.create_locations()
