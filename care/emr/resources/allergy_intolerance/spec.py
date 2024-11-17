import datetime
from enum import Enum

from pydantic import UUID4, Field

from care.emr.fhir.schema.base import CodeableConcept
from care.emr.models.allergy_intolerance import AllergyIntolerance
from care.emr.resources.allergy_intolerance.valueset import CARE_ALLERGY_CODE_VALUESET
from care.emr.resources.base import FHIRResource
from care.facility.models import PatientConsultation


class ClinicalStatusChoices(str, Enum):
    active = "active"
    inactive = "inactive"
    resolved = "resolved"


class VerificationStatusChoices(str, Enum):
    unconfirmed = "unconfirmed"
    presumed = "presumed"
    confirmed = "confirmed"
    refuted = "refuted"
    entered_in_error = "entered-in-error"


class CategoryChoices(str, Enum):
    food = "food"
    medication = "medication"
    environment = "environment"
    biologic = "biologic"


class CriticalityChoices(str, Enum):
    low = "low"
    high = "high"
    unable_to_assess = "unable-to-assess"


class AllergyIntoleranceOnSetSpec(FHIRResource):
    onset_datetime: datetime.datetime = None
    onset_age: int = None
    onset_string: str = None
    recorded_date: datetime.datetime | None = None
    last_occurrence: datetime.datetime | None = None
    note: str


class BaseAllergyIntoleranceSpec(FHIRResource):
    __model__ = AllergyIntolerance
    __exclude__ = ["patient", "encounter"]
    id: UUID4 = None


class AllergyIntoleranceSpec(BaseAllergyIntoleranceSpec):
    clinical_status: ClinicalStatusChoices
    verification_status: VerificationStatusChoices
    category: CategoryChoices
    criticality: CriticalityChoices
    code: CodeableConcept = Field(
        {}, json_schema_extra={"slug": CARE_ALLERGY_CODE_VALUESET.slug}
    )
    encounter: UUID4
    onset: AllergyIntoleranceOnSetSpec = {}

    def perform_extra_deserialization(self, is_update, obj):
        if not is_update:
            obj.encounter = PatientConsultation.objects.get(
                external_id=self.encounter
            )  # Needs more validation
            obj.patient = obj.encounter.patient


class AllergyIntrolanceSpecRead(BaseAllergyIntoleranceSpec):
    """
    Validation for deeper models may not be required on read, Just an extra optimisation
    """

    clinical_status: str
    verification_status: str
    category: str
    criticality: str
    code: dict
    onset: dict

    @classmethod
    def perform_extra_serialization(cls, mapping, obj):
        mapping["id"] = obj.external_id
