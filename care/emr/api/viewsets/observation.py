from django_filters import rest_framework as filters

from care.emr.api.viewsets.base import EMRModelReadOnlyViewSet
from care.emr.models.observation import Observation
from care.emr.resources.observation.spec import ObservationSpec


class MultipleCodeFilter(filters.CharFilter):
    def filter(self, qs, value):
        queryset = qs
        if value:
            queryset = queryset.filter(main_code__code__in=value.split(","))
        return queryset


class ObservationFilter(filters.FilterSet):
    encounter = filters.UUIDFilter(field_name="encounter__external_id")
    codes = MultipleCodeFilter()


class ObservationViewSet(EMRModelReadOnlyViewSet):
    database_model = Observation
    pydantic_model = ObservationSpec
    filterset_class = ObservationFilter
    filter_backends = [filters.DjangoFilterBackend]

    def get_queryset(self):
        queryset = (
            super()
            .get_queryset()
            .filter(patient__external_id=self.kwargs["patient_external_id"])
        )

        return queryset.order_by("-modified_date")
