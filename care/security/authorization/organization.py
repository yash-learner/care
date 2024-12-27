from care.security.authorization.base import (
    AuthorizationController,
    AuthorizationHandler,
)
from care.security.permissions.organization import OrganizationPermissions


class OrganizationAccess(AuthorizationHandler):
    def can_create_organization_obj(self, user, organization):
        """
        Check if the user has permission to create organizations under the given organization
        """
        return self.check_permission_in_organization(
            [OrganizationPermissions.can_create_organization.name],
            user,
            [*organization.parent_cache, organization.id],
        )

    def can_manage_organization_obj(self, user, organization):
        """
        Check if the user has permission to manage given organization.
        """
        return self.check_permission_in_organization(
            [OrganizationPermissions.can_manage_organization.name],
            user,
            [*organization.parent_cache, organization.id],
        )

    def can_manage_organization_users_obj(self, user, organization):
        """
        Check if the user has permission to create organizations under the given organization
        """
        return self.check_permission_in_organization(
            [OrganizationPermissions.can_manage_organization_users.name],
            user,
            [*organization.parent_cache, organization.id],
        )

    def can_list_organization_users_obj(self, user, organization):
        """
        Check if the user has permission to create organizations under the given organization
        """
        return self.check_permission_in_organization(
            [OrganizationPermissions.can_list_organization_users.name],
            user,
            [*organization.parent_cache, organization.id],
        )


AuthorizationController.register_internal_controller(OrganizationAccess)
