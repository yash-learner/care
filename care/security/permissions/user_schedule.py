import enum

from care.security.permissions.constants import Permission, PermissionContext
from care.security.roles.role import (
    ADMIN_ROLE,
    DOCTOR_ROLE,
    FACILITY_ADMIN_ROLE,
    NURSE_ROLE,
    STAFF_ROLE,
)


class UserSchedulePermissions(enum.Enum):
    can_write_user_schedule = Permission(
        "Can Create on User Schedule",
        "",
        PermissionContext.FACILITY,
        [ADMIN_ROLE, STAFF_ROLE, FACILITY_ADMIN_ROLE, DOCTOR_ROLE, NURSE_ROLE],
    )
    can_list_user_schedule = Permission(
        "Can Read on Facility",
        "",
        PermissionContext.FACILITY,
        [ADMIN_ROLE, STAFF_ROLE, FACILITY_ADMIN_ROLE, DOCTOR_ROLE, NURSE_ROLE],
    )
