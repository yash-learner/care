from django.db import models

from care.emr.models.base import EMRBaseModel
from care.facility.models.patient import PatientRegistration
from care.facility.models.patient_consultation import PatientConsultation
from care.users.models import User


class ServiceRequest(EMRBaseModel):
    status = models.CharField(max_length=100, null=True, blank=True)
    intent = models.CharField(max_length=100, null=True, blank=True)
    priority = models.CharField(max_length=100, null=True, blank=True)

    category = models.JSONField(null=True, blank=True)
    code = models.JSONField(default=dict, null=False, blank=False)

    do_not_perform = models.BooleanField(default=False)

    subject = models.ForeignKey(
        PatientRegistration,
        on_delete=models.CASCADE,
        related_name="service_request",
    )
    encounter = models.ForeignKey(
        PatientConsultation,
        on_delete=models.CASCADE,
        related_name="service_request",
    )

    occurrence_datetime = models.DateTimeField(null=True, blank=True)
    occurrence_timing = models.JSONField(default=dict, null=True, blank=True)
    as_needed = models.BooleanField(default=False)
    as_needed_for = models.JSONField(null=True, blank=True)

    authored_on = models.DateTimeField(null=True, blank=True)
    requester = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="requested_service_request"
    )

    location = models.UUIDField(
        null=True, blank=True
    )  # TODO: Make this a foreign key of emr.Organization once it is created

    note = models.JSONField(default=list, null=True, blank=True)
    patient_instruction = models.TextField(null=True, blank=True)

    replaces = models.ForeignKey(
        "self", on_delete=models.CASCADE, null=True, blank=True
    )
