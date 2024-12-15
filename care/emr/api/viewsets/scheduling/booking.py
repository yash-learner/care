from django_filters import CharFilter, FilterSet
from django_filters.rest_framework import DjangoFilterBackend

from care.emr.api.viewsets.base import (
    EMRBaseViewSet,
    EMRDeleteMixin,
    EMRListMixin,
    EMRRetrieveMixin,
    EMRUpdateMixin,
)
from care.emr.models import TokenBooking
from care.emr.resources.scheduling.slot.spec import TokenBookingReadSpec, TokenBookingUpdateSpec


class TokenBookingFilters(FilterSet):
    status = CharFilter(field_name="status")


class TokenBookingViewSet(
    EMRRetrieveMixin, EMRUpdateMixin, EMRListMixin, EMRDeleteMixin, EMRBaseViewSet
):
    database_model = TokenBooking
    pydantic_model = TokenBookingReadSpec
    pydantic_read_model = TokenBookingReadSpec
    pydantic_update_model = TokenBookingUpdateSpec

    filterset_class = TokenBookingFilters
    filter_backends = [DjangoFilterBackend]
    CREATE_QUESTIONNAIRE_RESPONSE = False

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .filter(token_slot__resource__facility__external_id=self.kwargs["facility_external_id"])
            .select_related(
                "token_slot",
                "patient",
                "token_slot__resource",
                "token_slot__resource__facility",
            )
            .order_by("-modified_date")
        )
