import uuid

from django.db import models

from care.emr.models import EMRBaseModel


class Questionnaire(EMRBaseModel):
    version = models.CharField(max_length=255)
    slug = models.CharField(max_length=255, default=uuid.uuid4, unique=True)
    title = models.CharField(max_length=255)
    description = models.TextField(default="")
    subject_type = models.CharField(max_length=255)
    status = models.CharField(max_length=255)
    styling_metadata = models.JSONField(default=dict)
    questions = models.JSONField(default=dict)


class QuestionnaireResponse(EMRBaseModel):
    questionnaire = models.ForeignKey(
        Questionnaire, on_delete=models.CASCADE, null=True, blank=True
    )
    subject_id = models.UUIDField()
    responses = models.JSONField(default=list)
    structured_responses = models.JSONField(default=dict)
    structured_response_type = models.CharField(default=None, blank=True, null=True)
    patient = models.ForeignKey(
        "facility.PatientRegistration", on_delete=models.CASCADE
    )
    encounter = models.ForeignKey(
        "facility.PatientConsultation", on_delete=models.CASCADE, null=True, blank=True
    )

    # TODO : Add index for subject_id and subject_type in descending order
