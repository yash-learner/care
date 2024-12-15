import datetime
import logging

from pydantic import UUID4, BaseModel
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from care.emr.api.viewsets.base import EMRModelReadOnlyViewSet
from care.emr.models.scheduling.booking import TokenSlot
from care.emr.models.scheduling.schedule import Availability, SchedulableResource
from care.emr.resources.scheduling.schedule.spec import (
    SlotTypeOptions,
)
from care.emr.resources.scheduling.slot.spec import TokenSlotBaseSpec
from care.users.models import User
from dateutil.parser import parse

from django.utils import timezone

class SlotsForDayRequestSpec(BaseModel):
    resource: UUID4
    resource_type: str = "user"
    day: datetime.date



def convert_availability_to_slots(availabilities):
    slots = {}
    for availability in availabilities:
        start_time = parse(availability["availability"]["start_time"])
        end_time = parse(availability["availability"]["end_time"])
        slot_size_in_minutes = availability["slot_size_in_minutes"]
        availability_id = availability["availability_id"]
        current_time = start_time
        i = 0
        while current_time < end_time:
            i+=1
            if i == 30:
                # Failsafe to prevent infinite loop
                break
            slots[f"{current_time.time()}-{(current_time + datetime.timedelta(minutes=slot_size_in_minutes)).time()}"] = {
                    "start_time": current_time.time(),
                    "end_time": (current_time + datetime.timedelta(minutes=slot_size_in_minutes)).time(),
                    "availability_id": availability_id,
                }

            current_time += datetime.timedelta(minutes=slot_size_in_minutes)
    return slots


class SlotViewSet(EMRModelReadOnlyViewSet):
    @action(detail=False, methods=["POST"])
    def get_slots_for_day(self, request, *args, **kwargs):
        facility = self.kwargs["facility_external_id"]
        request_data = SlotsForDayRequestSpec(**request.data)
        user = User.objects.filter(external_id=request_data.resource).first()
        if not user:
            raise ValidationError("Resource does not exist")
        schedulable_resource_obj = SchedulableResource.objects.filter(
            facility__external_id=facility,
            resource_id=user.id,
            resource_type=request_data.resource_type,
        ).first()
        if not schedulable_resource_obj:
            raise ValidationError("Resource is not schedulable")
        # Find all relevant schedules
        availabilities = Availability.objects.filter(
            slot_type=SlotTypeOptions.appointment.value,
            schedule__valid_from__lte=request_data.day,
            schedule__valid_to__gte=request_data.day,
            schedule__resource=schedulable_resource_obj,
        )
        # Fetch all availabilities for that day of week
        calculated_dow_availabilities = []
        for schedule_availability in availabilities:
            for day_availability in schedule_availability.availability:
                if day_availability["day_of_week"] == request_data.day.weekday():
                    calculated_dow_availabilities.append(
                        {
                            "availability": day_availability,
                            "slot_size_in_minutes": schedule_availability.slot_size_in_minutes,
                            "availability_id": schedule_availability.id,
                        }
                    )
        # Remove anything that has an availability exception
        logging.info(calculated_dow_availabilities)
        # Generate all slots already created for that day
        slots = convert_availability_to_slots(calculated_dow_availabilities)
        # Fetch all existing slots in that day
        created_slots = TokenSlot.objects.filter(start_datetime__date=request_data.day, end_datetime__date=request_data.day , resource=schedulable_resource_obj)
        logging.info(slots)
        for slot in created_slots:
            logging.info(slot.start_datetime)
            slot_key = f"{slot.start_datetime.time()}-{slot.end_datetime.time()}"
            logging.info(slot_key)
            if slot_key in slots:
                if slots[slot_key]["availability_id"] == slot.availability.id:
                    slots.pop(slot_key)

        # Create everything else
        for _slot in slots:
            slot = slots[_slot]
            a = TokenSlot.objects.create(
                resource=schedulable_resource_obj,
                start_datetime=datetime.datetime.combine(request_data.day, slot["start_time"] ,tzinfo=timezone.now().tzinfo),
                end_datetime=datetime.datetime.combine(request_data.day, slot["end_time"] ,tzinfo=timezone.now().tzinfo),
                availability_id=slot["availability_id"],
            )
            logging.info(slot["start_time"])
            logging.info(slot["end_time"])
            logging.info(a.start_datetime)
            logging.info(a.end_datetime)
        # Compare and figure out what needs to be created
        return Response({"results" : [ TokenSlotBaseSpec.serialize(slot).model_dump(exclude=["meta"]) for slot in TokenSlot.objects.filter(start_datetime__date=request_data.day, end_datetime__date=request_data.day , resource=schedulable_resource_obj).select_related("availability") ]})
        # Find all existing Slot objects for that period
        # Get list of all slots, create if missed
        # Return slots
