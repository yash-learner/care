from datetime import datetime

from pydantic import UUID4, BaseModel

from care.emr.fhir.schema.base import Coding
from care.emr.models.questionnaire import QuestionnaireResponse
from care.emr.resources.base import EMRResource


class QuestionnaireSubmitResultValue(BaseModel):
    value: str
    value_code: Coding = None


class QuestionnaireSubmitResult(BaseModel):
    question_id: UUID4
    body_site: Coding = None
    method: Coding = None
    taken_at: datetime = None
    values: list[QuestionnaireSubmitResultValue] = []
    note: str = None


class QuestionnaireSubmitRequest(BaseModel):
    resource_id: UUID4
    encounter: UUID4
    results: list[QuestionnaireSubmitResult]


class QuestionnaireResponseReadSpec(EMRResource):
    __model__ = QuestionnaireResponse

    subject_id: str
    responses: list
    encounter: str
    patient: str
