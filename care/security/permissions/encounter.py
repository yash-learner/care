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

ALL_ROLES = [
    ADMIN_ROLE,
    DOCTOR_ROLE,
    NURSE_ROLE,
    GEO_ADMIN,
    STAFF_ROLE,
    FACILITY_ADMIN_ROLE,
]


class EncounterPermissions(enum.Enum):
    can_write_encounter = Permission(
        "Can write encounter",
        "",
        PermissionContext.ENCOUNTER,
        ALL_ROLES,
    )
    can_list_encoutners = Permission(
        "Can list encounters",
        "",
        PermissionContext.ENCOUNTER,
        ALL_ROLES,
    )
