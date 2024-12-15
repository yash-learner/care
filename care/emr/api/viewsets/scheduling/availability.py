import datetime

from pydantic import BaseModel
from pydantic import UUID4
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from care.emr.api.viewsets.base import EMRModelViewSet, EMRModelReadOnlyViewSet
from care.emr.models.scheduling.schedule import SchedulableResource, Availability
from care.emr.resources.scheduling.schedule.spec import ResourceTypeOptions
from care.users.models import User
import logging


class SlotsForDayRequestSpec(BaseModel):
    resource : UUID4
    resource_type :str = "user"
    day : datetime.date

class SlotViewSet(EMRModelReadOnlyViewSet):



    @action(detail=False , methods=["POST"])
    def get_slots_for_day(self , request , *args, **kwargs):
        facility = self.kwargs["facility_external_id"]
        request_data = SlotsForDayRequestSpec(**request.data)
        user = User.objects.filter(external_id=request_data.resource).first()
        if not user:
            raise ValidationError("Resource does not exist")
        schedulable_resource_obj = SchedulableResource.objects.filter(facility__external_id=facility,resource_id=user.id , resource_type=request_data.resource_type).first()
        if not schedulable_resource_obj:
            raise ValidationError("Resource is not schedulable")
        # Find all relevant schedules
        schedules = Availability.objects.filter(schedule__valid_from__lte=request_data.day, schedule__valid_to__gte=request_data.day, schedule__resource=schedulable_resource_obj)
        logging.info(schedules)
        return Response({})
        # Find all existing Slot objects for that period
        # Get list of all slots, create if missed
        # Return slots
