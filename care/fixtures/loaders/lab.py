from care.emr.resources.location.spec import (
    FacilityLocationFormChoices,
    FacilityLocationModeChoices,
)
from care.fixtures.constants import LAB_TESTS, HealthcareServiceInternalType


def load_lab_definitions(base, facility_id, departments):
    laboratory = departments["Laboratory"]
    administration = departments.get("Administration")

    lab_location = base.create_location(
        facility_id,
        name="Bio-Chemistry Lab",
        form=FacilityLocationFormChoices.ro.value,
        mode=FacilityLocationModeChoices.kind.value,
        organizations=[laboratory.id],
    )
    base.add_organization_to_location(facility_id, lab_location.id, laboratory.id)
    if administration:
        base.add_organization_to_location(
            facility_id, lab_location.id, administration.id
        )

    lab_charge_category = base.create_resource_category(
        facility_id, "Lab Tests", "charge_item_definition"
    )
    lab_activity_category = base.create_resource_category(
        facility_id, "Lab Tests", "activity_definition"
    )

    lab_service = base.create_healthcare_service(
        facility_id,
        name="Pathology Lab",
        internal_type=HealthcareServiceInternalType.lab.value,
        styling_metadata={"careIcon": "microscope"},
        locations=[lab_location.id],
    )

    for test in LAB_TESTS:
        base.create_lab_test(
            facility_id,
            test,
            service_id=lab_service.id,
            location_id=lab_location.id,
            charge_category_slug=lab_charge_category.slug,
            activity_category_slug=lab_activity_category.slug,
        )
