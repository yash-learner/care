import datetime
from enum import Enum

from pydantic import UUID4, Field, field_validator

from care.emr.fhir.schema.base import Coding
from care.emr.models.condition import Condition
from care.emr.registries.care_valueset.care_valueset import validate_valueset
from care.emr.resources.base import EMRResource
from care.emr.resources.condition.valueset import CARE_CODITION_CODE_VALUESET
from care.facility.models import PatientConsultation


class ClinicalStatusChoices(str, Enum):
    active = "active"
    recurrence = "recurrence"
    relapse = "relapse"
    inactive = "inactive"
    remission = "remission"
    resolved = "resolved"
    unknown = "unknown"


class VerificationStatusChoices(str, Enum):
    unconfirmed = "unconfirmed"
    provisional = "provisional"
    differential = "differential"
    confirmed = "confirmed"
    refuted = "refuted"
    entered_in_error = "entered_in_error"


class CategoryChoices(str, Enum):
    problem_list_item = "problem_list_item"
    encounter_diagnosis = "encounter-diagnosis"


class SeverityChoices(str, Enum):
    mild = "mild"
    moderate = "moderate"
    severe = "severe"


class ConditionOnSetSpec(EMRResource):
    onset_datetime: datetime.datetime = None
    onset_age: int = None
    onset_string: str = None
    note: str


class BaseAllergyIntoleranceSpec(EMRResource):
    __model__ = Condition
    __exclude__ = ["patient", "encounter"]
    id: UUID4 = None


class ConditionSpec(BaseAllergyIntoleranceSpec):
    clinical_status: ClinicalStatusChoices
    verification_status: VerificationStatusChoices
    category: CategoryChoices
    severity: SeverityChoices
    code: Coding = Field(json_schema_extra={"slug": CARE_CODITION_CODE_VALUESET.slug})
    encounter: UUID4
    onset: ConditionOnSetSpec = {}

    @field_validator("code")
    @classmethod
    def validate_code(cls, code: int) -> int:
        return validate_valueset(
            "code", cls.model_fields["code"].json_schema_extra["slug"], code
        )

    def perform_extra_deserialization(self, is_update, obj):
        if not is_update:
            obj.encounter = PatientConsultation.objects.get(
                external_id=self.encounter
            )  # Needs more validation
            obj.patient = obj.encounter.patient


class ConditionSpecRead(BaseAllergyIntoleranceSpec):
    """
    Validation for deeper models may not be required on read, Just an extra optimisation
    """

    # Maybe we can use model_construct() to be better at reads, need profiling to be absolutely sure
    clinical_status: str
    verification_status: str
    category: str
    criticality: str
    code: Coding
    onset: ConditionOnSetSpec = dict

    @classmethod
    def perform_extra_serialization(cls, mapping, obj):
        mapping["id"] = obj.external_id
