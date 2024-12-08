from django.db import models

from care.emr.models.base import EMRBaseModel


class DiagnosticReport(EMRBaseModel):
    status = models.CharField(max_length=100, null=True, blank=True)

    category = models.JSONField(null=True, blank=True)
    code = models.JSONField(default=dict, null=False, blank=False)

    based_on = models.ForeignKey(
        "emr.ServiceRequest", on_delete=models.CASCADE
    )  # TODO: Make it GenericForeignKey when needed
    subject = models.ForeignKey(
        "facility.PatientRegistration", on_delete=models.CASCADE
    )
    encounter = models.ForeignKey(
        "facility.PatientConsultation", on_delete=models.CASCADE
    )

    performer = models.ForeignKey("users.User", on_delete=models.CASCADE)
    results_interpreter = models.ForeignKey("users.User", on_delete=models.CASCADE)

    issued = models.DateTimeField(null=True, blank=True)
    effective_period = models.JSONField(null=True, blank=True)

    specimen = models.ManyToManyField("emr.Specimen", blank=True)
    result = models.ManyToManyField("emr.Observation", blank=True)

    media = models.JSONField(default=list, null=True, blank=True)

    conclusion = models.TextField(null=True, blank=True)

    note = models.JSONField(default=list, null=True, blank=True)
