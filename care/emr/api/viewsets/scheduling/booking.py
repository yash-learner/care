from django_filters import CharFilter, FilterSet, UUIDFilter
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.decorators import action
from rest_framework.response import Response

from care.emr.api.viewsets.base import (
    EMRBaseViewSet,
    EMRDeleteMixin,
    EMRListMixin,
    EMRRetrieveMixin,
    EMRUpdateMixin,
)
from care.emr.models import SchedulableResource, TokenBooking
from care.emr.resources.scheduling.slot.spec import (
    TokenBookingReadSpec,
    TokenBookingRetrieveSpec,
    TokenBookingUpdateSpec,
)
from care.emr.resources.user.spec import UserSpec
from care.facility.models import Facility, FacilityUser


class TokenBookingFilters(FilterSet):
    status = CharFilter(field_name="status")
    patient = UUIDFilter(field_name="patient__external_id")


class TokenBookingViewSet(
    EMRRetrieveMixin, EMRUpdateMixin, EMRListMixin, EMRDeleteMixin, EMRBaseViewSet
):
    database_model = TokenBooking
    pydantic_model = TokenBookingReadSpec
    pydantic_read_model = TokenBookingReadSpec
    pydantic_update_model = TokenBookingUpdateSpec
    pydantic_retrieve_model = TokenBookingRetrieveSpec

    filterset_class = TokenBookingFilters
    filter_backends = [DjangoFilterBackend]
    CREATE_QUESTIONNAIRE_RESPONSE = False

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .filter(
                token_slot__resource__facility__external_id=self.kwargs[
                    "facility_external_id"
                ]
            )
            .select_related(
                "token_slot",
                "patient",
                "token_slot__resource",
                "token_slot__resource__facility",
            )
            .order_by("-modified_date")
        )

    @action(detail=False, methods=["GET"])
    def available_doctors(self, request, *args, **kwargs):
        facility = Facility.objects.get(external_id=self.kwargs["facility_external_id"])
        facility_users = FacilityUser.objects.filter(
            user_id__in=SchedulableResource.objects.filter(facility=facility).values(
                "resource_id"
            ),
            facility=facility,
        )

        return Response(
            {
                "users": [
                    UserSpec.serialize(facility_user.user).model_dump(exclude=["meta"])
                    for facility_user in facility_users
                ]
            }
        )
