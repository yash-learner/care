from care.emr.api.viewsets.base import EMRBaseViewSet, EMRBaseController
from care.emr.models.allergy_intolerance import AllergyIntolerance
from care.emr.resources.allergy_intolerance.spec import AllergyIntoleranceSpec


class AllergyIntolleranceController(EMRBaseController):
    database_model = AllergyIntolerance
    pydantic_model = AllergyIntoleranceSpec


class AllergyIntoleranceViewset(EMRBaseViewSet):
    emr_controller = AllergyIntolleranceController
