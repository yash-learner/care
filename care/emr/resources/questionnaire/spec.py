from enum import Enum
from typing import Any

from pydantic import UUID4, ConfigDict, Field

from care.emr.fhir.schema.base import Coding
from care.emr.models import Questionnaire
from care.emr.resources.base import EMRResource


class EnableOperator(str, Enum):
    exists = "exists"
    equals = "equals"
    not_equals = "not_equals"
    greater = "greater"
    less = "less"
    greater_or_equals = "greater_or_equals"
    less_or_equals = "less_or_equals"


class EnableBehavior(str, Enum):
    all = "all"
    any = "any"


class DisabledDisplay(str, Enum):
    hidden = "hidden"
    protected = "protected"


class QuestionType(str, Enum):
    group = "group"
    boolean = "boolean"
    decimal = "decimal"
    integer = "integer"
    string = "string"
    text = "text"
    date = "date"
    datetime = "dateTime"
    time = "time"
    choice = "choice"
    open_choice = "open_choice"
    attachment = "attachment"
    reference = "reference"
    quantity = "quantity"


class AnswerConstraint(str, Enum):
    required = "required"
    optional = "optional"


class QuestionnaireStatus(str, Enum):
    active = "active"
    retired = "retired"
    draft = "draft"


class SubjectType(str, Enum):
    patient = "patient"
    encounter = "encounter"


class QuestionnaireBaseSpec(EMRResource):
    __model__ = Questionnaire


class Performer(QuestionnaireBaseSpec):
    performer_type: str = Field(
        alias="performerType", description="Type of performer from FHIR specification"
    )
    performer_id: str | None = Field(
        alias="performerId", description="ID of the reference"
    )
    text: str | None = Field(
        description="Text description when no hard reference exists"
    )


class EnableWhen(QuestionnaireBaseSpec):
    question: str = Field(description="Link ID of the question to check against")
    operator: EnableOperator
    answer: Any = Field(description="Value for operator, based on question type")


class AnswerOption(QuestionnaireBaseSpec):
    value: Any = Field(description="Value based on question type")
    initial_selected: bool = Field(
        alias="initialSelected",
        default=False,
        description="Whether option is initially selected",
    )


class Question(QuestionnaireBaseSpec):
    model_config = ConfigDict(populate_by_name=True)

    link_id: str = Field(
        alias="link_id", description="Unique human readable ID for linking"
    )
    id: UUID4 = Field(description="Unique machine provided UUID")
    code: Coding | None = Field(description="Coding for observation creation")
    collect_time: bool = Field(
        alias="collectTime", default=False, description="Whether to collect timestamp"
    )
    collect_performer: bool = Field(
        default=False,
        description="Whether to collect performer",
    )
    text: str = Field(description="Question text")
    type: QuestionType
    enable_when: list[EnableWhen] | None = Field(alias="enableWhen", default=None)
    enable_behavior: EnableBehavior | None = Field(alias="enableBehavior", default=None)
    disabled_display: DisabledDisplay | None = Field(
        alias="disabledDisplay", default=None
    )
    collect_body_site: bool | None = Field(alias="collectBodySite", default=None)
    collect_method: bool | None = Field(alias="collectMethod", default=None)
    required: bool | None = None
    repeats: bool | None = None
    read_only: bool | None = None
    max_length: int | None = None
    answer_constraint: AnswerConstraint | None = Field(
        alias="answerConstraint", default=None
    )
    answer_option: list[AnswerOption] | None = Field(alias="answerOption", default=None)
    answer_value_set: str | None = None
    is_observation: bool | None = None
    questions: list["Question"] | None = None
    formula: str | None = None


class QuestionnaireSpec(QuestionnaireBaseSpec):
    version: str = Field("1.0", frozen=True, description="Version of the questionnaire")
    title: str
    description: str = ""
    status: QuestionnaireStatus
    subject_type: SubjectType
    styling_metadata: dict = Field(
        {}, description="Styling requirements without validation"
    )
    questions: list[Question]


class QuestionnaireReadSpec(QuestionnaireBaseSpec):
    id: str
    version: str
    title: str
    description: str = ""
    status: QuestionnaireStatus
    subject_type: SubjectType
    styling_metadata: dict
    questions: list

    @classmethod
    def perform_extra_serialization(cls, mapping, obj):
        mapping["id"] = obj.external_id


# Add this to handle recursive Question type
Question.model_rebuild()
