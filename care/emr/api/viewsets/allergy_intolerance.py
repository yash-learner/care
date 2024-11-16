from care.emr.api.viewsets.base import EMRBaseViewSet
from care.emr.models.allergy_intolerance import AllergyIntolerance
from care.emr.resources.allergy_intolerance.spec import AllergyIntoleranceSpec


class AllergyIntoleranceViewSet(EMRBaseViewSet):
    database_model = AllergyIntolerance
    pydantic_model = AllergyIntoleranceSpec

    def clean_create_data(self, request, *args, **kwargs):
        data = request.data
        data["encounter"] = kwargs["consultation_external_id"]
        return data

    def get_queryset(self):
        return super().get_queryset().select_related("patient", "encounter")
