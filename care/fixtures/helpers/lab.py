from django.urls import reverse

from care.fixtures.helpers.utils import slugify


class LabFixturesMixin:
    """Lab & observation definitions, charge item definitions, and the
    composite ``create_lab_test``."""

    def create_specimen_definition(self, facility_id, title, **kwargs):
        url = reverse(
            "specimen_definition-list",
            kwargs={"facility_external_id": facility_id},
        )
        data = {
            "title": title,
            "status": "active",
            "description": "",
            "type_collected": {},
            "slug_value": slugify(title),
            **kwargs,
        }
        return self.post(url, data)

    def create_observation_definition(
        self,
        title,
        code,
        category,
        permitted_data_type,
        qualified_ranges,
        facility=None,
        **kwargs,
    ):
        data = {
            "title": title,
            "status": "active",
            "description": "",
            "category": category,
            "code": code,
            "permitted_data_type": permitted_data_type,
            "qualified_ranges": qualified_ranges,
            "slug_value": slugify(title),
            **kwargs,
        }
        if facility:
            data["facility"] = facility
        return self.post(reverse("observation_definition-list"), data)

    def create_healthcare_service(self, facility_id, name, **kwargs):
        url = reverse(
            "healthcare_service-list",
            kwargs={"facility_external_id": facility_id},
        )
        if "extra_details" not in kwargs:
            kwargs["extra_details"] = ""
        data = {
            "name": name,
            "managing_organization": None,
            **kwargs,
        }
        return self.post(url, data)

    def create_charge_item_definition(
        self, facility_id, title, price_components, **kwargs
    ):
        url = reverse(
            "charge_item_definition-list",
            kwargs={"facility_external_id": facility_id},
        )
        data = {
            "status": "active",
            "title": title,
            "slug_value": slugify(title),
            "price_components": price_components,
            "can_edit_charge_item": True,
            "discount_configuration": None,
            **kwargs,
        }
        return self.post(url, data)

    def create_activity_definition(
        self,
        facility_id,
        title,
        code,
        locations,
        specimen_requirements,
        observation_result_requirements,
        charge_item_definitions,
        **kwargs,
    ):
        url = reverse(
            "activity_definition-list",
            kwargs={"facility_external_id": facility_id},
        )
        data = {
            "title": title,
            "status": "active",
            "classification": "laboratory",
            "kind": "service_request",
            "code": code,
            "slug_value": slugify(title),
            "locations": locations,
            "specimen_requirements": specimen_requirements,
            "observation_result_requirements": observation_result_requirements,
            "charge_item_definitions": charge_item_definitions,
            "healthcare_service": None,
            **kwargs,
        }
        return self.post(url, data)

    def create_lab_test(
        self,
        facility_id,
        test,
        service_id,
        location_id,
        charge_category_slug,
        activity_category_slug,
    ):
        """Create a complete lab test: specimen -> observation -> charge_item_definition -> activity_definition."""

        specimen = self.create_specimen_definition(facility_id, **test["specimen"])
        observation = self.create_observation_definition(
            facility=facility_id, **test["observation"]
        )
        charge_item_definition = self.create_charge_item_definition(
            facility_id,
            category=charge_category_slug,
            **test["charge_item_definition"],
        )

        activity_config = {**test["activity"]}
        self.create_activity_definition(
            facility_id,
            locations=[location_id],
            specimen_requirements=[specimen.slug],
            observation_result_requirements=[observation.slug],
            charge_item_definitions=[charge_item_definition.slug],
            healthcare_service=service_id,
            category=activity_category_slug,
            **activity_config,
        )
