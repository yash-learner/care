from care.emr.api.viewsets.base import EMRBaseViewSet
from care.emr.models.allergy_intolerance import AllergyIntolerance
from care.emr.resources.allergy_intolerance.spec import AllergyIntoleranceSpec


class AllergyIntoleranceViewset(EMRBaseViewSet):
    database_model = AllergyIntolerance
    pydantic_model = AllergyIntoleranceSpec
