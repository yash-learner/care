from care.emr.resources.organization.spec import OrganizationTypeChoices
from care.fixtures.constants import MANAGING_ORG_USERS


def setup_managing_organization(base, role_orgs, geo_id, password):
    """Create a managing organization, link it to all role orgs, and assign users."""
    role_org_roles = base.get_role_org_roles()

    managing_org = base.create_organization(
        org_type=OrganizationTypeChoices.role.value, name="Health Department"
    )
    managing_org_id = managing_org.id

    for _name, org in role_orgs.items():
        base.link_managing_org(org.id, managing_org_id)

    for user_def in MANAGING_ORG_USERS:
        role_id = role_org_roles[user_def["role"]].id

        if user_def["action"] == "create":
            user = base.create_user(
                geo_id,
                username=user_def["username"],
                email=f"{user_def['username']}@care.test",
                password=password,
            )
            base.assign_org_role(managing_org_id, user.id, role_id)

        elif user_def["action"] == "assign":
            user_data = base.get_user(user_def["username"])
            base.assign_org_role(managing_org_id, user_data.id, role_id)
