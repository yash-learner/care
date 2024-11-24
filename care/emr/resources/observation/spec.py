from datetime import datetime
from enum import Enum

from pydantic import UUID4, BaseModel, Field

from care.emr.fhir.schema.base import CodeableConcept
from care.emr.resources.base import EMRResource
from care.emr.resources.questionnaire.spec import SubjectType


class ObservationStatus(str, Enum):
    final = "final"
    amended = "amended"


class PerformerType(str, Enum):
    related_person = "related_person"
    user = "user"


class Coding(BaseModel):
    system: str
    code: str
    text: str | None = None


class Performer(BaseModel):
    type: PerformerType
    id: str


class ReferenceRange(BaseModel):
    low: float | None = None
    high: float | None = None
    unit: str | None = None
    text: str | None = None


class ObservationSpec(EMRResource):
    id: str = Field(description="Unique ID in the system")

    status: ObservationStatus = Field(
        description="Status of the observation (final or amended)"
    )

    category: list[CodeableConcept] = Field(
        ..., description="List of codeable concepts derived from the questionnaire"
    )

    main_code: Coding = Field(
        ..., description="Code for the observation (LOINC binding)"
    )

    alternate_coding: CodeableConcept = dict

    subject_type: SubjectType

    encounter: UUID4

    effective_datetime: datetime = Field(
        ...,
        description="Datetime when observation was recorded",
    )

    data_entered_by: int

    performer: Performer | None = Field(
        None,
        description="Who performed the observation (currently supports RelatedPerson)",
    )  # If none the observation is captured by the data entering person

    value: str | None = Field(
        None,
        description="Value of the observation if not code. For codes, contains display text",
    )

    value_code: Coding | None = Field(
        None, description="Value as code part of a system"
    )

    note: str | None = Field(None, description="Additional notes about the observation")

    body_site: Coding | None = Field(
        None, description="Body site where observation was made"
    )  # TODO Add Valueset

    method: Coding | None = Field(
        None, description="Method used for the observation"
    )  # TODO Add Valueset

    reference_range: list[ReferenceRange] = Field(
        [], description="Reference ranges for interpretation"
    )

    interpretation: str | None = Field(
        None, description="Interpretation based on the reference range"
    )

    parent: UUID4 | None = Field(None, description="ID reference to parent observation")
