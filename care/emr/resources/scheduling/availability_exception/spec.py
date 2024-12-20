import datetime
from enum import Enum

from django.core.exceptions import ObjectDoesNotExist
from pydantic import UUID4
from rest_framework.exceptions import ValidationError

from care.emr.models import AvailabilityException
from care.emr.models.scheduling.schedule import (
    SchedulableResource,
)
from care.emr.resources.base import EMRResource
from care.facility.models import Facility
from care.users.models import User


class ResourceTypeOptions(str, Enum):
    user = "user"


class AvailabilityExceptionBaseSpec(EMRResource):
    __model__ = AvailabilityException
    __exclude__ = ["resource", "facility"]

    id: UUID4 | None = None
    reason: str | None = None
    valid_from: datetime.date
    valid_to: datetime.date
    start_time: datetime.time
    end_time: datetime.time


class AvailabilityExceptionWriteSpec(AvailabilityExceptionBaseSpec):
    facility: UUID4 | None = None
    resource: UUID4
    resource_type: ResourceTypeOptions = ResourceTypeOptions.user

    def perform_extra_deserialization(self, is_update, obj):
        if not is_update:
            resource = None
            if self.resource_type == ResourceTypeOptions.user:
                try:
                    user_resource = User.objects.get(external_id=self.resource)
                    resource = SchedulableResource.objects.get(
                        resource_id=user_resource.id,
                        resource_type="user",
                        facility=Facility.objects.get(external_id=self.facility),
                    )
                    obj.resource = resource
                except ObjectDoesNotExist as e:
                    raise ValidationError("Object does not exist") from e


class AvailabilityExceptionReadSpec(AvailabilityExceptionBaseSpec):
    @classmethod
    def perform_extra_serialization(cls, mapping, obj):
        mapping["id"] = obj.external_id
