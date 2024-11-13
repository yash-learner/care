import datetime
from enum import Enum

from pydantic import UUID4, BaseModel

from care.emr.fhir.schema.base import CodeableConcept
from care.emr.models.allergy_intolerance import AllergyIntolerance
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


class AllergyIntoleranceOnSetSpec(BaseModel):
    onsetDateTime: datetime.datetime = None
    onsetAge: int = None
    onsetString: str = None


class AllergyIntoleranceSpec(FHIRResource):
    id: UUID4 = None
    clinical_status: ClinicalStatusChoices
    verification_status: VerificationStatusChoices
    category: CategoryChoices
    criticality: CriticalityChoices
    code: CodeableConcept = None
    patient: UUID4 = None
    encounter: UUID4
    onset: AllergyIntoleranceOnSetSpec = {}
    recorded_date: datetime.datetime = None
    last_occurrence: datetime.datetime = None
    note: str

    @classmethod
    def from_database(cls, obj: AllergyIntolerance):
        return cls(
            id=obj.external_id,
            clinical_status=obj.clinical_status,
            verification_status=obj.verification_status,
            category=obj.category,
            criticality=obj.criticality,
            code=obj.code,
            patient=obj.patient.external_id,
            encounter=obj.encounter.external_id,
            onset=obj.onset,
            # recorded_date=obj.recorded_date,
            last_occurance=obj.last_occurrence,
            note=obj.note
        )

    def to_orm_object(self, obj=None):
        if not obj:
            obj = AllergyIntolerance()
            obj.encounter = PatientConsultation.objects.get(external_id=self.encounter) # Needs more validation
            obj.patient = obj.encounter.patient
        obj.clinical_status = self.clinical_status
        obj.verification_status = self.verification_status
        obj.category = self.category
        obj.criticality = self.criticality
        obj.onset = self.onset
        obj.recorded_date = self.recorded_date
        obj.last_occurrence = self.last_occurrence
        obj.note = self.note
        return obj
