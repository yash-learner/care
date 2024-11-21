from drf_spectacular.utils import extend_schema, extend_schema_view

from care.emr.api.viewsets.base import EMRModelViewSet
from care.emr.models.allergy_intolerance import AllergyIntolerance
from care.emr.resources.allergy_intolerance.spec import (
    AllergyIntoleranceSpec,
    AllergyIntrolanceSpecRead,
)


@extend_schema_view(
    create=extend_schema(request=AllergyIntoleranceSpec),
)
class AllergyIntoleranceViewSet(EMRModelViewSet):
    database_model = AllergyIntolerance
    pydantic_model = AllergyIntoleranceSpec
    pydantic_read_model = AllergyIntrolanceSpecRead

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .filter(patient__external_id=self.kwargs["patient_external_id"])
            .select_related("patient", "encounter")
        )
