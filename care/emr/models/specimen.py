from django.db import models

from care.emr.models.base import EMRBaseModel


class Specimen(EMRBaseModel):
    accession_identifier = models.CharField(max_length=100, null=True, blank=True)

    status = models.CharField(max_length=100, null=True, blank=True)

    type = models.JSONField(default=dict, null=False, blank=False)

    subject = models.ForeignKey(
        "facility.PatientRegistration", on_delete=models.CASCADE
    )
    request = models.ForeignKey("emr.ServiceRequest", on_delete=models.CASCADE)

    collected_by = models.ForeignKey(
        "users.User", on_delete=models.CASCADE, null=True, blank=True
    )
    collected_at = models.DateTimeField(null=True, blank=True)

    processing = models.JSONField(default=list, null=True, blank=True)

    note = models.JSONField(default=list, null=True, blank=True)
