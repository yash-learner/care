from django.contrib.postgres.fields import ArrayField
from django.db import models

from care.emr.models import EMRBaseModel


class FacilityOrganization(EMRBaseModel):
    active = models.BooleanField(default=True)
    root_org = models.ForeignKey(
        "self", on_delete=models.CASCADE, related_name="root", null=True, blank=True
    )
    org_type = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    facility = models.ForeignKey("facility.Facility", on_delete=models.CASCADE)
    system_generated = models.BooleanField(default=False)
    parent = models.ForeignKey(
        "self", related_name="children", on_delete=models.CASCADE, null=True, blank=True
    )
    level_cache = models.IntegerField(default=0)
    parent_cache = ArrayField(models.IntegerField(), default=list)


class Organization(EMRBaseModel):
    active = models.BooleanField(default=True)
    root_org = models.ForeignKey(
        "self", on_delete=models.CASCADE, related_name="root", null=True, blank=True
    )
    org_type = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    level_cache = models.IntegerField(default=0)
    system_generated = models.BooleanField(default=False)
    parent_cache = ArrayField(models.IntegerField(), default=list)
    parent = models.ForeignKey(
        "self", related_name="children", on_delete=models.CASCADE, null=True, blank=True
    )


class OrganizationUser(EMRBaseModel):
    """
    This model represents how an organization can access an entity,
    ex, Organization can access Patients through role X,
    This does not mean that the organization has access to all patients,
    only the ones assigned to them. when assigning the organization the user has an
    option to override the role to give or take permissions.
    """

    organization = models.ForeignKey("Organization", on_delete=models.CASCADE)
    user = models.ForeignKey("users.User", on_delete=models.CASCADE)
    role = models.ForeignKey("security.RoleModel", on_delete=models.CASCADE)


class FacilityOrganizationUser(EMRBaseModel):
    """
    Same as OrganizationContextRole but for facility scoped organizations
    """

    organization = models.ForeignKey("FacilityOrganization", on_delete=models.CASCADE)
    user = models.ForeignKey("users.User", on_delete=models.CASCADE)
    role = models.ForeignKey("security.RoleModel", on_delete=models.CASCADE)
