import enum

from care.security.permissions.constants import Permission, PermissionContext
from care.security.roles.role import (
    ADMIN_ROLE,
    DOCTOR_ROLE,
    GEO_ADMIN,
    NURSE_ROLE,
    STAFF_ROLE,
)


class PatientPermissions(enum.Enum):
    can_list_patients = Permission(
        "Can list patients",
        "",
        PermissionContext.PATIENT,
        [STAFF_ROLE, DOCTOR_ROLE, NURSE_ROLE, GEO_ADMIN, ADMIN_ROLE],
    )
