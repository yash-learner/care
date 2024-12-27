import json
import logging
from datetime import UTC, datetime
from pathlib import Path

from django.core.management.base import BaseCommand

from care.emr.models.organziation import Organization

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """ """

    help = ""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.migration_id = int(datetime.now(tz=UTC).timestamp() * 1000)

    def add_arguments(self, parser):
        parser.add_argument(
            "--overwrite",
            default=False,
            action="store_true",
            help="Overwrite the data if already present",
        )
        parser.add_argument("json_file_path", help="path to the folder of JSONs")

    def load_data(self):
        with self.json_file_path.open() as json_file:
            data = json.load(json_file)

        state_defaults = {
            "active": True,
            "org_type": "govt",
            "description": "",
            "has_children": True,
            "system_generated": True,
            "level_cache": 0,
            "metadata": {
                "country": "india",
                "govt_org_type": "state",
                "migration_id": self.migration_id,
            },
        }

        for item in data:
            state_name = item["state"].strip()

            districts = [d.strip() for d in item["districts"].split(",")]

            if self.overwrite:
                state, _ = Organization.objects.update_or_create(
                    name__iexact=state_name,
                    defaults={"name": state_name, **state_defaults},
                )
            else:
                state, _ = Organization.objects.get_or_create(
                    name__iexact=state_name,
                    defaults={"name": state_name, **state_defaults},
                )
            logger.debug("State: %s", state.id)

            district_defaults = {
                "active": True,
                "parent": state,
                "org_type": "govt",
                "description": "",
                "has_children": True,
                "system_generated": True,
                "level_cache": 1,
                "metadata": {
                    "country": "india",
                    "govt_org_type": "district",
                    "migration_id": self.migration_id,
                },
            }

            for d in districts:
                if self.overwrite:
                    district, _ = Organization.objects.update_or_create(
                        parent=state,
                        name__iexact=d,
                        defaults={"name": d, **district_defaults},
                    )
                else:
                    district, _ = Organization.objects.get_or_create(
                        parent=state,
                        name__iexact=d,
                        defaults={"name": d, **district_defaults},
                    )
                district.get_parent_json()
                logger.debug("District: %s", district.id)

    def handle(self, *args, **options):
        if options["verbosity"] == 0:
            logger.setLevel(logging.ERROR)
        elif options["verbosity"] == 1:
            logger.setLevel(logging.INFO)
        else:
            logger.setLevel(logging.DEBUG)

        self.json_file_path = Path(options["json_file_path"])
        self.overwrite = options["overwrite"]

        logger.info("Loading Govt Organization Data")
        logger.info("Migration ID: %s", self.migration_id)
        logger.info("Overwrite: %s", self.overwrite)

        self.load_data()

        logger.info("Data Loaded")
