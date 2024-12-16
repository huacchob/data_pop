"""Location creation job."""

import csv
import typing as t

from django.core.exceptions import ValidationError
from django.db.models.fields.files import FieldFile
from nautobot.apps.jobs import FileVar, Job
from nautobot.dcim.models import LocationType

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

    class Meta:
        """Meta class."""

        name: str = "Create Locations"

    def __init__(self, *args, **kwargs) -> None:
        """Initialize Job."""
        super().__init__(*args, **kwargs)
        self.csv_file: FieldFile
        self.locations: t.List[t.Dict[str, str]]

    def find_state_abbr(self, state_two_letters: str) -> t.Optional[str]:
        """Find the state based on the two letter code.

        Args:
            state_two_letters (str): state two letter code.

        Returns:
            t.Optional[str]: state if found.
        """
        return STATE_ABBREVIATIONS.get(state_two_letters)

    def get_location_type(self, site_name: str) -> LocationType | None:
        """Get location type.

        Args:
            site_name (str): site name.

        Returns:
            LocationType | None: locationType if found.
        """
        location_type: t.Optional[LocationType] = None

        if site_name.endswith("-DC"):
            location_type = LocationType.objects.get(
                name="Data Center",
            )
        elif site_name.endswith("-BR"):
            location_type = LocationType.objects.get(name="Branch")

        if location_type:
            return location_type
        else:
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

    def run(self, **data: t.Any) -> None:
        """Run the job."""
        self.csv_file = data["csv_file"]
        self.parse_csv()
        self.logger.info(
            msg="self.locations: {locations}".format(locations=self.locations),
            extra={"grouping": "initialization"},
        )
        # state_location_type = LocationType.objects.get(name="State")
        # city_location_type = LocationType.objects.get(name="City")
        # active_status_object = Status.objects.get(name="Active")
        # for row in self.locations:
        #     # Find the state based on the two letter code
        #     state = self.find_state_abbr(row["state"])

        #     # Get the object, create if it doesn't exsist
        #     state_object, state_obj_created = Location.objects.get_or_create(
        #         name=state,
        #         defaults={
        #             "name": state,
        #             "status": active_status_object,
        #             "location_type": state_location_type,
        #         },
        #     )
        #     # We also need the city object
        #     city_object, city_obj_created = Location.objects.get_or_create(
        #         name=row["city"],
        #         defaults={
        #             "name": row["city"],
        #             "status": active_status_object,
        #             "parent": state_object,
        #             "location_type": city_location_type,
        #         },
        #     )
        #     location_type = self.get_location_type(row["name"])
        #     site_object, created = Location.objects.get_or_create(
        #         name=row["name"],
        #         defaults={
        #             "name": row["name"],
        #             "status": active_status_object,
        #             "location_type": location_type,
        #             "parent": city_object,
        #         },
        #     )
        #     if created:
        #         self.logger.info(
        #             f"Created the Following Entry - State: {state}, Site Name: {row['name']}, Location Type: {location_type}"
        #         )
        #     else:
        #         self.logger.info("Location already Exists")
