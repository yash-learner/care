from rest_framework.exceptions import ValidationError

from care.emr.api.viewsets.base import EMRModelReadOnlyViewSet
from care.emr.models.observation import Observation
from care.emr.resources.observation.spec import ObservationSpec


class ObservationViewSet(EMRModelReadOnlyViewSet):
    database_model = Observation
    pydantic_model = ObservationSpec

    def get_queryset(self):
        queryset = super().get_queryset()
        if "encounter" in self.request.GET:
            queryset = queryset.filter(
                encounter__external_id=self.request.GET["encounter"]
            )
        elif "patient" in self.request.GET:
            queryset = queryset.filter(patient__external_id=self.request.GET["patient"])
        else:
            raise ValidationError({"patient": "required"})
        return queryset.order_by("-modified_date")
