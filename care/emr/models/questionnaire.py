from django.db import models

from care.emr.models import EMRBaseModel


class Questionnaire(EMRBaseModel):
    version = models.CharField(max_length=255)
    title = models.CharField(max_length=255)
    description = models.TextField(default="")
    subject_type = models.CharField(max_length=255)
    status = models.CharField(max_length=255)
    styling_metadata = models.JSONField(default=dict)
    questions = models.JSONField(default=dict)
