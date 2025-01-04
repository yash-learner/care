import logging
from csv import DictReader
from datetime import UTC, datetime
from typing import NamedTuple

import requests
from django.core.management.base import BaseCommand
from django.db import transaction

from care.emr.models import Organization

logger = logging.getLogger(__name__)


class RowObj(NamedTuple):
    state: str
    district: str
    local_body: str
    local_body_type: str
    ward_number: int
    ward_name: str


type OrgDict = dict[
    str,  # state
    dict[
        str,  # district
        dict[
            str,  # local_body
            dict[
                str,  # local_body_type
                dict[
                    int,  # ward_number
                    str,  # ward_name
                ],
            ],
        ],
    ],
]


class Command(BaseCommand):
    """
    Load Govt Organizations from CSV
    The script takes in a CSV file with the following columns:
    - State
    - District
    - Local Body
    - Local Body Type
    - Ward Number
    - Ward Name
    """

    help = "Load Govt Organizations from CSV."

    def add_arguments(self, parser):
        parser.add_argument("csv_file_url", type=str, help="CSV File URL")

    def read_csv(self, url: str) -> list[RowObj]:
        logger.info("Reading CSV from %s", url)
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = set()
        duplicates = []
        logger.info("Parsing CSV")
        reader = DictReader(response.text.splitlines())
        expected_columns = {
            "State",
            "District",
            "Local Body",
            "Local Body Type",
            "Ward Number",
            "Ward Name",
        }
        if set(reader.fieldnames) != expected_columns:
            logger.error("Invalid CSV Columns: %s", reader.fieldnames)
            raise ValueError("Invalid CSV Columns")
        for row in DictReader(response.text.splitlines()):
            row_obj = RowObj(
                state=row["State"].strip(),
                district=row["District"].strip(),
                local_body=row["Local Body"].strip(),
                local_body_type=row["Local Body Type"].strip(),
                ward_number=int(row["Ward Number"].strip()),
                ward_name=row["Ward Name"].strip(),
            )
            if row_obj in data:
                duplicates.append(row_obj)
            data.add(row_obj)
        if duplicates:
            logger.error("Duplicate rows found: %s", duplicates)
            raise ValueError("Duplicate rows found")
        logger.info("Sorting Data")
        sorted_data = sorted(
            data, key=lambda x: (x.state, x.district, x.local_body, x.ward_number)
        )
        logger.info("Rows Parsed: %s", len(sorted_data))
        return sorted_data

    def rows_to_dict(self, rows: list[RowObj]) -> OrgDict:
        # convert rows to nested dict
        # {
        #     "state": {
        #         "district": {
        #             "local_body": {
        #                 "local_body_type": {
        #                     "ward_number": "ward_name"
        #                 }
        #             }
        #         }
        #     }
        # }
        logger.info("Converting Rows to Dict")
        data = {}
        for row in rows:
            state: dict = data.setdefault(row.state, {})
            district: dict = state.setdefault(row.district, {})
            local_body: dict = district.setdefault(row.local_body, {})
            local_body_type: dict = local_body.setdefault(row.local_body_type, {})
            local_body_type[row.ward_number] = row.ward_name
        return data

    def create_organization(self, data: OrgDict):
        logger.info("Creating Organizations")
        for state, districts in data.items():
            state_obj, created = Organization.objects.filter(
                name__iexact=state,
                org_type="govt",
                metadata={"country": "India", "govt_org_type": "state"},
            ).get_or_create(
                defaults={
                    "name": state,
                    "org_type": "govt",
                    "system_generated": True,
                    "metadata": {"country": "India", "govt_org_type": "state"},
                    "meta": {"migration_id": self.timestamp},
                },
            )
            logger.debug(
                "State: %s, Created: %s, State ID: %s",
                state,
                created,
                state_obj.id,
            )
            for district, local_bodies in districts.items():
                district_obj, created = Organization.objects.filter(
                    name__iexact=district,
                    parent=state_obj,
                    org_type="govt",
                    metadata={"country": "India", "govt_org_type": "district"},
                ).get_or_create(
                    defaults={
                        "name": district,
                        "root_org": state_obj,
                        "parent": state_obj,
                        "org_type": "govt",
                        "system_generated": True,
                        "metadata": {"country": "India", "govt_org_type": "district"},
                        "meta": {"migration_id": self.timestamp},
                    },
                )
                logger.debug(
                    "District: %s, Created: %s, District ID: %s",
                    district,
                    created,
                    district_obj.id,
                )
                for local_body, local_body_types in local_bodies.items():
                    for local_body_type, wards in local_body_types.items():
                        lb_type = local_body_type.lower().replace(" ", "_")
                        local_body_obj, created = Organization.objects.filter(
                            name__iexact=local_body,
                            parent=district_obj,
                            org_type="govt",
                            metadata={"country": "India", "govt_org_type": lb_type},
                        ).get_or_create(
                            defaults={
                                "name": local_body,
                                "root_org": state_obj,
                                "parent": district_obj,
                                "org_type": "govt",
                                "system_generated": True,
                                "metadata": {
                                    "country": "India",
                                    "govt_org_type": lb_type,
                                },
                                "meta": {"migration_id": self.timestamp},
                            },
                        )
                        logger.debug(
                            "Local Body: %s, Created: %s, Local Body ID: %s",
                            local_body,
                            created,
                            local_body_obj.id,
                        )
                        for ward_number, ward_name in wards.items():
                            ward_obj, created = Organization.objects.get_or_create(
                                name__iexact=ward_name,
                                parent=local_body_obj,
                                org_type="govt",
                                metadata={
                                    "country": "India",
                                    "govt_org_type": "ward",
                                    "govt_org_id": ward_number,
                                },
                                defaults={
                                    "name": ward_name,
                                    "root_org": state_obj,
                                    "parent": local_body_obj,
                                    "org_type": "govt",
                                    "system_generated": True,
                                    "metadata": {
                                        "country": "India",
                                        "govt_org_type": "ward",
                                        "govt_org_id": ward_number,
                                    },
                                    "meta": {"migration_id": self.timestamp},
                                },
                            )
                            logger.debug(
                                "Ward: %s, Created: %s, Ward ID: %s",
                                ward_name,
                                created,
                                ward_obj.id,
                            )

    def handle(self, *args, **options):
        start_time = datetime.now(tz=UTC)
        if options["verbosity"] == 0:
            logger.setLevel(logging.ERROR)
        elif options["verbosity"] == 1:
            logger.setLevel(logging.INFO)
        else:
            logger.setLevel(logging.DEBUG)

        self.timestamp = int(start_time.timestamp() * 1000)

        csv_file_url = options["csv_file_url"]
        data = self.rows_to_dict(self.read_csv(csv_file_url))

        with transaction.atomic():
            self.create_organization(data)

        self.stdout.write(self.style.SUCCESS(f"migration_id: {self.timestamp}"))
        self.stdout.write(
            self.style.SUCCESS(f"Time taken: {datetime.now(tz=UTC) - start_time}")
        )
        self.stdout.write(self.style.SUCCESS("Successfully loaded Govt Organizations."))
