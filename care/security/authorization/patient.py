from care.emr.models.organziation import OrganizationUser
from care.security.authorization.base import (
    AuthorizationController,
    AuthorizationHandler,
)
from care.security.permissions.patient import PatientPermissions


class PatientAccess(AuthorizationHandler):
    def get_filtered_patients(self, qs, user):
        if user.is_superuser:
            return qs
        roles = self.get_role_from_permissions(
            [PatientPermissions.can_list_patients.name]
        )
        organization_ids = list(
            OrganizationUser.objects.filter(user=user, role_id__in=roles).values_list(
                "organization_id", flat=True
            )
        )
        return qs.filter(organization_cache__overlap=organization_ids)


AuthorizationController.register_internal_controller(PatientAccess)
