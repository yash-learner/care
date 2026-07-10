from care.emr.resources.encounter.constants import StatusChoices
from care.emr.resources.location.spec import (
    FacilityLocationFormChoices,
    FacilityLocationModeChoices,
)
from care.emr.resources.organization.spec import OrganizationTypeChoices
from care.fixtures.constants import FACILITY_DEPARTMENTS, MANAGING_ORG_USERS
from care.fixtures.context import care_fixture_context
from care.fixtures.loaders.billing import load_billing
from care.fixtures.loaders.inventory import load_inventory
from care.fixtures.loaders.lab import load_lab_definitions
from care.fixtures.loaders.managing_org import setup_managing_organization
from care.fixtures.loaders.scheduling import load_scheduling


def log(message):
    print(message)  # noqa: T201


def load_fixtures(base):  # noqa: PLR0915, PLR0912
    password = "Ohcn@123"

    geo_organization = base.create_organization(
        org_type=OrganizationTypeChoices.govt.value, name="Kerala"
    )
    base.create_organization(
        org_type=OrganizationTypeChoices.govt.value,
        parent=geo_organization.id,
        name="Ernakulam",
    )
    suppliers = []
    for _ in range(3):
        suppliers.append(
            base.create_organization(
                org_type=OrganizationTypeChoices.product_supplier.value,
                name=f"Supplier {base.fake.company()}",
            )
        )
    role_org_names = [
        "Volunteer",
        "Doctor",
        "Staff",
        "Nurse",
        "Administrator",
        "Facility Admin",
    ]
    role_orgs = {}
    for name in role_org_names:
        role_orgs[name] = base.create_organization(
            org_type=OrganizationTypeChoices.role.value, name=name
        )
    log("Loading organizations completed")

    facility = base.create_facility(
        geo_organization.id,
        name="FACILITY WITH PATIENTS",
        facility_type="Private Hospital",
    )
    facility_id = facility.id
    log("Loading facility completed")

    existing = base.get_facility_organizations(facility_id)
    departments = {}
    admin_org = next((o for o in existing if o.name == "Administration"), None)
    if admin_org:
        departments["Administration"] = admin_org
    for name in FACILITY_DEPARTMENTS:
        departments[name] = base.create_facility_organization(facility_id, name=name)
    general_medicine = departments["General Medicine"]
    log("Loading departments completed")

    ward = base.create_location(
        facility_id,
        name="Ward A",
        form=FacilityLocationFormChoices.wa.value,
        mode=FacilityLocationModeChoices.kind.value,
        organizations=[general_medicine.id],
    )
    for idx in range(1, 6):
        base.create_location(
            facility_id,
            name=f"Bed {idx}",
            description=f"Bed {idx} in {ward.name}",
            parent=ward.id,
            form=FacilityLocationFormChoices.bd.value,
            mode=FacilityLocationModeChoices.instance.value,
            organizations=[general_medicine.id],
        )
    log("Loading locations completed")

    for i in range(1, 6):
        base.create_device(facility_id, registered_name=f"Device {i}")
    log("Loading devices completed")

    roles = base.get_roles()
    default_users = [
        ("Doctor", "care-doctor"),
        ("Staff", "care-staff"),
        ("Nurse", "care-nurse"),
        ("Administrator", "care-admin"),
        ("Volunteer", "care-volunteer"),
        ("Facility Admin", "care-fac-admin"),
    ]
    created_users = {}
    for role_name, username in default_users:
        if role_name not in roles or role_name not in role_orgs:
            continue
        user = base.create_user(
            geo_organization.id,
            role_orgs=[
                {
                    "organization": role_orgs[role_name].id,
                    "role": roles[role_name].id,
                }
            ],
            username=username,
            email=f"{username}@care.test",
            password=password,
        )
        created_users[role_name] = user
    log("Loading users completed")

    patients = []
    for _ in range(10):
        patients.append(base.create_patient(geo_organization.id))
    log("Loading patients completed")

    encounters = {}
    for patient in patients:
        encounters[patient.id] = base.create_encounter(
            patient.id,
            facility_id,
            organizations=[general_medicine.id],
            status=StatusChoices.in_progress.value,
        )
    log("Loading encounters completed")

    admin_org = departments.get("Administration")
    if admin_org:
        for role_name in ("Facility Admin", "Nurse", "Staff"):
            user = created_users.get(role_name)
            role = roles.get(role_name)
            if user and role:
                base.add_user_to_facility_organization(
                    facility_id, admin_org.id, user.id, role.id
                )
    log("Loading facility organization memberships completed")

    base.create_facility(
        geo_organization.id,
        name="SECONDARY FACILITY",
        facility_type="Private Hospital",
        is_public=True,
    )
    log("Loading secondary facility completed")

    base.load_questionnaires_from_file([geo_organization.id])
    log("Loading questionnaires completed")

    base.load_templates_from_file(facility=facility_id)
    log("Loading report templates completed")

    load_lab_definitions(base, facility_id, departments)
    log("Loading lab definitions completed")

    load_inventory(base, facility_id, departments, suppliers, ward)
    log("Loading inventory completed")

    # Billing seeds build charge items from lab-test / medicine / consumable
    # charge item definitions, so it must run after those are created.
    load_billing(base, facility_id, patients, encounters)
    log("Loading billing (accounts, charge items, invoices) completed")

    load_scheduling(base, facility_id, created_users, patients, departments, roles)
    log("Loading scheduling completed")

    setup_managing_organization(base, role_orgs, geo_organization.id, password)
    log("Loading managing organization completed")

    log("\n" + "=" * 55)
    log(f"  {'Username':<25} {'Password':<15} {'Role'}")
    log("-" * 55)
    log(f"  {'admin':<25} {'admin':<15} {'Superuser'}")
    for role_name, username in default_users:
        log(f"  {username:<25} {password:<15} {role_name}")
    for user_def in MANAGING_ORG_USERS:
        if user_def["action"] == "create":
            log(f"  {user_def['username']:<25} {password:<15} {user_def['role']}")
    log("=" * 55 + "\n")


if __name__ == "__main__":
    with care_fixture_context() as base:
        load_fixtures(base)
