from care.emr.models.questionnaire import QuestionnaireResponse
from care.emr.resources.base import EMRResource


class QuestionnaireResponseReadSpec(EMRResource):
    __model__ = QuestionnaireResponse

    subject_id: str
    responses: list
    encounter: str
    patient: str
