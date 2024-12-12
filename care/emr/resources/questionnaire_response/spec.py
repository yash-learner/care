from datetime import datetime

from pydantic import UUID4, BaseModel

from care.emr.models.questionnaire import QuestionnaireResponse
from care.emr.resources.base import EMRResource
from care.emr.resources.common import Coding, Quantity
from care.emr.resources.questionnaire.spec import QuestionnaireReadSpec


class QuestionnaireSubmitResultValue(BaseModel):
    value: str | None = None
    value_code: Coding | None = None
    value_quantity: Quantity | None = None


class QuestionnaireSubmitResult(BaseModel):
    question_id: UUID4
    body_site: Coding | None = None
    method: Coding | None = None
    taken_at: datetime | None = None
    values: list[QuestionnaireSubmitResultValue] = []
    note: str | None = None


class QuestionnaireSubmitRequest(BaseModel):
    resource_id: UUID4
    encounter: UUID4
    results: list[QuestionnaireSubmitResult]


class QuestionnaireResponseReadSpec(EMRResource):
    __model__ = QuestionnaireResponse

    id: UUID4
    questionnaire: QuestionnaireReadSpec
    subject_id: str
    responses: list
    encounter: str
    patient: str

    @classmethod
    def perform_extra_serialization(cls, mapping, obj):
        mapping["id"] = obj.external_id
        mapping["questionnaire"] = QuestionnaireReadSpec.serialize(obj.questionnaire)
