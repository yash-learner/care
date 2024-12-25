from datetime import datetime, timedelta

from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.utils import timezone

from care.emr.models import EMRBaseModel

class OrganizationCommonBase(EMRBaseModel):
    active = models.BooleanField(default=True)
    root_org = models.ForeignKey(
        "self", on_delete=models.CASCADE, related_name="root", null=True, blank=True
    )
    org_type = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    has_children = models.BooleanField(default=False)
    description = models.TextField(blank=True, null=True)
    system_generated = models.BooleanField(default=False)
    parent = models.ForeignKey(
        "self", related_name="children", on_delete=models.CASCADE, null=True, blank=True
    )
    level_cache = models.IntegerField(default=0)
    parent_cache = ArrayField(models.IntegerField(), default=list)
    metadata = models.JSONField(default=dict)
    cached_parent_json = models.JSONField(default=dict)
    cache_expiry_days = 15
    # Storing parent data within the organization to save joins each time

    def get_parent_json(self):
        if self.parent:
            if self.cached_parent_json and timezone.now() < datetime.fromisoformat(
                self.cached_parent_json["cache_expiry"]
            ):
                return self.cached_parent_json
            if self.parent:
                self.parent.get_parent_json()
            self.cached_parent_json = {
                "id": str(self.parent.external_id),
                "name": self.parent.name,
                "description": self.parent.description,
                "org_type": self.parent.org_type,
                "metadata": self.parent.metadata,
                "parent": self.parent.cached_parent_json,
                "level_cache": self.parent.level_cache,
                "cache_expiry": str(
                    timezone.now() + timedelta(days=self.cache_expiry_days)
                ),
            }
            self.save(update_fields=["cached_parent_json"])
            return self.cached_parent_json
        return {}


    class Meta:
        abstract = True


class FacilityOrganization(OrganizationCommonBase):

    facility = models.ForeignKey("facility.Facility", on_delete=models.CASCADE)



class Organization(OrganizationCommonBase):


    pass


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
