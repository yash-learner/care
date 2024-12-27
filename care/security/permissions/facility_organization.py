import enum

from care.security.permissions.constants import Permission, PermissionContext
from care.security.roles.role import (
    ADMIN_ROLE,
    DOCTOR_ROLE,
    FACILITY_ADMIN_ROLE,
    GEO_ADMIN,
    NURSE_ROLE,
    STAFF_ROLE,
)


class FacilityOrganizationPermissions(enum.Enum):
    can_create_facility_organization = Permission(
        "Can Create Facility Organizations",
        "",
        PermissionContext.FACILITY_ORGANIZATION,
        [FACILITY_ADMIN_ROLE],
    )
    can_list_facility_organization_users = Permission(
        "Can List Users in a Facility Organizations",
        "",
        PermissionContext.FACILITY_ORGANIZATION,
        [
            FACILITY_ADMIN_ROLE,
            STAFF_ROLE,
            DOCTOR_ROLE,
            NURSE_ROLE,
            ADMIN_ROLE,
            GEO_ADMIN,
        ],
    )
