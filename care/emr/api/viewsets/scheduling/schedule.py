from django.db import transaction
from django_filters import FilterSet, UUIDFilter
from django_filters.rest_framework import DjangoFilterBackend

from care.emr.api.viewsets.base import EMRModelViewSet
from care.emr.models.scheduling.schedule import Schedule
from care.emr.resources.scheduling.schedule.spec import (
    ScheduleReadSpec,
    ScheduleWriteSpec,
)


class ScheduleFilters(FilterSet):
    resource = UUIDFilter(field_name="resource__resource__external_id")


class ScheduleViewSet(EMRModelViewSet):
    database_model = Schedule
    pydantic_model = ScheduleWriteSpec
    pydantic_read_model = ScheduleReadSpec
    filterset_class = ScheduleFilters
    filter_backends = [DjangoFilterBackend]
    CREATE_QUESTIONNAIRE_RESPONSE = False

    def perform_create(self, instance):
        with transaction.atomic():
            super().perform_create(instance)
            for availability in instance.availabilities:
                availability_obj = availability.de_serialize()
                availability_obj.schedule = instance
                availability_obj.save()

    def clean_create_data(self, request_data):
        request_data["facility"] = self.kwargs["facility_external_id"]
        return request_data

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .filter(resource__facility__external_id=self.kwargs["facility_external_id"])
            .select_related("resource", "created_by", "updated_by")
            .order_by("-modified_date")
        )
