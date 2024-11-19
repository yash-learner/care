from care.emr.api.viewsets.base import EMRModelViewSet
from care.emr.models import Questionnaire
from care.emr.resources.questionnaire.spec import (
    QuestionnaireReadSpec,
    QuestionnaireSpec,
)


class QuestionnaireViewSet(EMRModelViewSet):
    database_model = Questionnaire
    pydantic_model = QuestionnaireSpec
    pydantic_read_model = QuestionnaireReadSpec
