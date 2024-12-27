from care.security.authorization.base import (
    AuthorizationController,
    AuthorizationHandler,
)
from care.security.permissions.facility_organization import (
    FacilityOrganizationPermissions,
)


class FacilityOrganizationAccess(AuthorizationHandler):
    def can_list_facility_organization_users_obj(self, user, organization):
        """
        Check if the user has permission to create organizations under the given organization
        """
        return self.check_permission_in_facility_organization(
            [
                FacilityOrganizationPermissions.can_list_facility_organization_users.value
            ],
            user,
            [*organization.parent_cache, organization.id],
        )


AuthorizationController.register_internal_controller(FacilityOrganizationAccess)
