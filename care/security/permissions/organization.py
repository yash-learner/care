import enum

from care.security.permissions.constants import Permission, PermissionContext
from care.security.roles.role import (
    ADMIN_ROLE,
    GEO_ADMIN,
)


class OrganizationPermissions(enum.Enum):
    can_create_organization = Permission(
        "Can Create Organizations",
        "",
        PermissionContext.ORGANIZATION,
        [ADMIN_ROLE],
    )
    can_manage_organization = Permission(
        "Can Manage Organizations",
        "This includes changing names, descriptions, metadata, etc..",
        PermissionContext.ORGANIZATION,
        [ADMIN_ROLE],
    )
    can_manage_organization_users = Permission(
        "Can Manage Users in an Organizations",
        "",
        PermissionContext.ORGANIZATION,
        [ADMIN_ROLE, GEO_ADMIN],
    )
    can_list_organization_users = Permission(
        "Can List Users in an Organizations",
        "",
        PermissionContext.ORGANIZATION,
        [ADMIN_ROLE, GEO_ADMIN],
    )
