from care.emr.models import EMRBaseModel

from django.db import models

class FacilityOrganization(EMRBaseModel):

    active = models.BooleanField(default=True)
    org_type = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    facility = models.ForeignKey('facility.Facility', on_delete=models.CASCADE)

    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True)
