import uuid
from enum import Enum
from typing import Any

from pydantic import UUID4, ConfigDict, Field, model_validator

from care.emr.fhir.schema.base import Coding
from care.emr.models import Questionnaire
from care.emr.resources.base import EMRResource
from care.emr.resources.observation.valueset import CARE_OBSERVATION_VALUSET


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
    display = "display"
    date = "date"
    datetime = "dateTime"
    time = "time"
    choice = "choice"
    # open_choice = "open_choice" # noqa ERA001
    url = "url"
    # attachment = "attachment" # noqa ERA001
    # reference = "reference" # noqa ERA001
    # quantity = "quantity" # noqa ERA001
    structured = "structured"


class AnswerConstraint(str, Enum):
    required = "required"
    optional = "optional"


class QuestionnaireStatus(str, Enum):
    active = "active"
    retired = "retired"
    draft = "draft"


class SubjectType(str, Enum):
    patient = "patient"


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
    id: UUID4 = Field(
        description="Unique machine provided UUID", default_factory=uuid.uuid4
    )
    code: Coding | None = Field(
        None,
        description="Coding for observation creation",
        json_schema_extra={"slug": CARE_OBSERVATION_VALUSET.slug},
    )
    collect_time: bool = Field(
        alias="collectTime", default=False, description="Whether to collect timestamp"
    )
    collect_performer: bool = Field(
        default=False,
        description="Whether to collect performer",
    )
    text: str = Field(description="Question text")
    description: str | None = Field(None, description="Question description")
    type: QuestionType
    structured_type: str | None = None  # TODO : Add validation later
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
    questions: list["Question"] = []
    formula: str | None = None
    styling_metadata: dict = {}

    def get_all_ids(self):
        ids = []
        for question in self.questions:
            ids.append({"id": question.id, "link_id": question.link_id})
            if question.questions:
                ids.extend(question.get_all_ids())
        return ids

    @model_validator(mode="after")
    def validate_options_not_empty(self):
        if self.type == QuestionType.choice and not self.answer_option:
            err = "Answer options are required for choice type questions"
            raise ValueError(err)
        return self


class QuestionnaireSpec(QuestionnaireBaseSpec):
    version: str = Field("1.0", frozen=True, description="Version of the questionnaire")
    slug: str | None = None
    title: str
    description: str = ""
    type: str = "custom"
    status: QuestionnaireStatus
    subject_type: SubjectType
    styling_metadata: dict = Field(
        {}, description="Styling requirements without validation"
    )
    questions: list[Question]

    def get_all_ids(self):
        ids = []
        for question in self.questions:
            ids.append({"id": question.id, "link_id": question.link_id})
            if question.questions:
                ids.extend(question.get_all_ids())
        return ids

    @model_validator(mode="after")
    def validate_unique_id(self):
        # Get all link and question id's and check for uniqueness
        ids = self.get_all_ids()
        link_ids = [id["link_id"] for id in ids]
        if len(link_ids) != len(set(link_ids)):
            err = "Link IDs must be unique"
            raise ValueError(err)
        ids = [id["id"] for id in ids]
        if len(ids) != len(set(ids)):
            err = "Question IDs must be unique"
            raise ValueError(err)
        return self


class QuestionnaireReadSpec(QuestionnaireBaseSpec):
    id: str
    slug: str | None = None
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
