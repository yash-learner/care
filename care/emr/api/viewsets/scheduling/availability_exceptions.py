from django_filters import FilterSet, UUIDFilter
from django_filters.rest_framework import DjangoFilterBackend

from care.emr.api.viewsets.base import EMRModelViewSet
from care.emr.models import AvailabilityException
from care.emr.resources.scheduling.availability_exception.spec import (
    AvailabilityExceptionReadSpec,
    AvailabilityExceptionWriteSpec,
)


class AvailabilityExceptionFilters(FilterSet):
    resource = UUIDFilter(field_name="resource__resource__external_id")


class AvailabilityExceptionsViewSet(EMRModelViewSet):
    database_model = AvailabilityException
    pydantic_model = AvailabilityExceptionWriteSpec
    pydantic_read_model = AvailabilityExceptionReadSpec
    filterset_class = AvailabilityExceptionFilters
    filter_backends = [DjangoFilterBackend]
    CREATE_QUESTIONNAIRE_RESPONSE = False

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
