import datetime
from enum import Enum

from pydantic import UUID4, Field

from care.emr.models.scheduling.booking import TokenSlot
from care.emr.models.scheduling.schedule import (
    Availability,
    SchedulableResource,
    Schedule,
)
from care.emr.resources.base import EMRResource
from care.emr.resources.user.spec import UserSpec
from care.facility.models import Facility
from care.users.models import User

class AvailabilityforTokenSpec(EMRResource):
    __model__ = Availability

    id: UUID4 | None = None
    name: str
    tokens_per_slot: int


class TokenSlotBaseSpec(EMRResource):
    __model__ = TokenSlot
    __exclude__ = ["resource" , "availability"]

    id: UUID4 | None = None
    availability: UUID4
    start_datetime: datetime.datetime
    end_datetime: datetime.datetime
    allocated: int


    @classmethod
    def perform_extra_serialization(cls, mapping, obj):
        mapping["id"] = obj.external_id
        mapping["availability"] = {"name" : obj.availability.name , "tokens_per_slot" : obj.availability.tokens_per_slot}

