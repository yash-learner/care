from django.db import models

from care.emr.models import EMRBaseModel


class ValueSet(EMRBaseModel):
    slug = models.SlugField(max_length=255, unique=True, db_index=True)
    name = models.CharField(max_length=255)
    description = models.TextField(default="")
    compose = models.JSONField(default=dict)
    status = models.CharField(max_length=255)
    is_system_defined = models.BooleanField(default=False)
