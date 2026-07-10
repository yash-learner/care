import json
from pathlib import Path
from secrets import choice

from django.urls import reverse

from care.emr.resources.device.spec import (
    DeviceAvailabilityStatusChoices,
    DeviceStatusChoices,
)
from care.emr.resources.encounter.constants import (
    ClassChoices,
    EncounterPriorityChoices,
)
from care.emr.resources.encounter.constants import (
    StatusChoices as EncounterStatusChoices,
)
from care.emr.resources.location.spec import (
    FacilityLocationFormChoices,
    FacilityLocationModeChoices,
    FacilityLocationOperationalStatusChoices,
)
from care.emr.resources.location.spec import StatusChoices as LocationStatusChoices
from care.emr.resources.patient.spec import BloodGroupChoices, GenderChoices
from care.facility.models.facility import REVERSE_FACILITY_TYPES, FacilityFeature
from care.fixtures.helpers.utils import FixtureError, generate_phone_number, slugify


class CoreFixturesMixin:
    """Organizations, facilities, locations, devices, users, patients,
    encounters, questionnaires, and resource categories."""

    def create_organization(self, org_type="govt", **kwargs):
        data = {
            "name": self.fake.state() if org_type == "govt" else self.fake.company(),
            "org_type": org_type,
            "active": True,
            **kwargs,
        }
        return self.post(reverse("organization-list"), data)

    def create_facility(self, geo_organization, **kwargs):
        data = {
            "name": self.fake.company() + " Hospital",
            "description": self.fake.paragraph(),
            "facility_type": choice(list(REVERSE_FACILITY_TYPES.values())),
            "address": self.fake.address(),
            "pincode": self.fake.random_int(min=100000, max=999999),
            "phone_number": generate_phone_number(),
            "latitude": float(self.fake.latitude()),
            "longitude": float(self.fake.longitude()),
            "is_public": self.fake.boolean(),
            "geo_organization": geo_organization,
            "features": [choice([f.value for f in FacilityFeature])],
            **kwargs,
        }
        return self.post(reverse("facility-list"), data)

    def get_facility_organizations(self, facility_id):
        url = reverse(
            "facility-organization-list",
            kwargs={"facility_external_id": facility_id},
        )
        data = self.get(url)
        return data.get("results", [])

    def create_facility_organization(self, facility_id, **kwargs):
        url = reverse(
            "facility-organization-list",
            kwargs={"facility_external_id": facility_id},
        )
        data = {
            "name": self.fake.bs().title(),
            "org_type": "team",
            "active": True,
            "description": self.fake.sentence(),
            **kwargs,
        }
        return self.post(url, data)

    def add_user_to_facility_organization(
        self, facility_id, facility_organization_id, user_id, role_id
    ):
        url = reverse(
            "facility-organization-users-list",
            kwargs={
                "facility_external_id": facility_id,
                "facility_organizations_external_id": facility_organization_id,
            },
        )
        return self.post(url, {"user": user_id, "role": role_id})

    def create_location(self, facility_id, **kwargs):
        url = reverse("location-list", kwargs={"facility_external_id": facility_id})
        data = {
            "name": f"Location {self.fake.random_uppercase_letter()}",
            "description": self.fake.sentence(),
            "form": FacilityLocationFormChoices.bd.value,
            "status": LocationStatusChoices.active.value,
            "operational_status": FacilityLocationOperationalStatusChoices.O.value,
            "mode": FacilityLocationModeChoices.instance.value,
            **kwargs,
        }
        return self.post(url, data)

    def add_organization_to_location(self, facility_id, location_id, organization_id):
        url = reverse(
            "location-organizations-add",
            kwargs={
                "facility_external_id": facility_id,
                "external_id": location_id,
            },
        )
        return self.post(url, {"organization": organization_id})

    def create_device(self, facility_id, **kwargs):
        url = reverse("device-list", kwargs={"facility_external_id": facility_id})
        data = {
            "registered_name": self.fake.word().title() + " Device",
            "status": DeviceStatusChoices.active.value,
            "availability_status": DeviceAvailabilityStatusChoices.available.value,
            "identifier": f"DEV-{self.fake.unique.random_int(min=1000, max=9999)}",
            **kwargs,
        }
        return self.post(url, data)

    def get_roles(self):
        data = self.get(reverse("role-list"))
        results = data.get("results", data)
        return {role.name: role for role in results}

    def create_user(self, geo_organization, role_orgs=None, **kwargs):
        data = {
            "username": self.fake.user_name(),
            "first_name": self.fake.first_name(),
            "last_name": self.fake.last_name(),
            "email": self.fake.email(),
            "password": "Ohcn@123",
            "phone_number": generate_phone_number(),
            "gender": GenderChoices.male.value,
            "geo_organization": geo_organization,
            "role_orgs": role_orgs or [],
            **kwargs,
        }
        return self.post(reverse("users-list"), data)

    def create_patient(self, geo_organization, **kwargs):
        data = {
            "name": self.fake.name(),
            "gender": choice([g.value for g in GenderChoices]),
            "phone_number": generate_phone_number(),
            "geo_organization": geo_organization,
            "address": self.fake.address(),
            "pincode": self.fake.random_int(min=100000, max=999999),
            "date_of_birth": self.fake.date_of_birth(
                minimum_age=18, maximum_age=80
            ).isoformat(),
            "blood_group": choice(
                [b.value for b in BloodGroupChoices if b.value != "unknown"]
            ),
            **kwargs,
        }
        return self.post(reverse("patient-list"), data)

    def create_encounter(self, patient_id, facility_id, organizations=None, **kwargs):
        data = {
            "patient": patient_id,
            "facility": facility_id,
            "status": choice(
                [s.value for s in EncounterStatusChoices if s.value != "unknown"]
            ),
            "encounter_class": choice([c.value for c in ClassChoices]),
            "priority": choice([p.value for p in EncounterPriorityChoices]),
            "organizations": organizations or [],
            **kwargs,
        }
        return self.post(reverse("encounter-list"), data)

    def create_questionnaire(self, organizations, data):
        questionnaire_data = {**data, "organizations": organizations}
        return self.post(reverse("questionnaire-list"), questionnaire_data)

    def load_questionnaires_from_file(
        self, organizations, path="data/questionnaire_fixtures.json"
    ):
        fixture_path = Path(path)
        if not fixture_path.exists():
            return []
        with fixture_path.open() as f:
            questionnaires = json.load(f)
        results = []
        for questionnaire_data in questionnaires:
            try:
                result = self.create_questionnaire(organizations, questionnaire_data)
                results.append(result)
            except FixtureError:
                pass
        return results

    def create_resource_category(self, facility_id, title, resource_type, **kwargs):
        url = reverse(
            "resource_category-list",
            kwargs={"facility_external_id": facility_id},
        )
        data = {
            "title": title,
            "resource_type": resource_type,
            "resource_sub_type": "other",
            "slug_value": slugify(f"{title}-{resource_type}"),
            **kwargs,
        }
        return self.post(url, data)
