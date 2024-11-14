from django.db import models

from care.utils.models.base import BaseModel


class EMRBaseModel(BaseModel):
    history = models.JSONField(default=dict)

    class Meta:
        abstract = True
