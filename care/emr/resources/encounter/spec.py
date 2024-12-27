# Not Being used
import datetime

from pydantic import UUID4, BaseModel, model_validator

from care.emr.models import Encounter, TokenBooking
from care.emr.models.patient import Patient
from care.emr.resources.base import EMRResource
from care.emr.resources.encounter.constants import (
    AdmitSourcesChoices,
    ClassChoices,
    DietPreferenceChoices,
    DischargeDispositionChoices,
    EncounterPriorityChoices,
    StatusChoices,
)
from care.emr.resources.patient.spec import PatientListSpec
from care.emr.resources.scheduling.slot.spec import TokenBookingReadSpec
from care.emr.resources.user.spec import UserSpec


class PeriodSpec(BaseModel):
    start: datetime.datetime | None = None
    end: datetime.datetime | None = None

    @model_validator(mode="after")
    def validate_period(self):
        if (self.start and self.end) and (self.start > self.end):
            raise ValueError("Start Date cannot be greater than End Date")
        return self


class HospitalizationSpec(BaseModel):
    re_admission: bool | None = None
    admit_source: AdmitSourcesChoices | None = None
    discharge_disposition: DischargeDispositionChoices | None = None
    diet_preference: DietPreferenceChoices | None = None


class EncounterSpecBase(EMRResource):
    __model__ = Encounter
    __exclude__ = ["patient", "organizations", "facility", "appointment"]

    id: UUID4 = None
    status: StatusChoices
    encounter_class: ClassChoices
    period: PeriodSpec = {}
    hospitalization: HospitalizationSpec | None = {}
    priority: EncounterPriorityChoices
    external_identifier: str | None = None


class EncounterCreateSpec(EncounterSpecBase):
    patient: UUID4
    organizations: list[UUID4] = []
    appointment: UUID4 | None = None

    def perform_extra_deserialization(self, is_update, obj):
        if not is_update:
            obj.patient = Patient.objects.get(external_id=self.patient)
            if self.appointment:
                obj.appointment = TokenBooking.objects.get(external_id=self.appointment)
            obj._organizations = list(set(self.organizations))  # noqa SLF001


class EncounterUpdateSpec(EncounterSpecBase):
    pass


class EncounterListSpec(EncounterSpecBase):
    patient: dict

    @classmethod
    def perform_extra_serialization(cls, mapping, obj):
        mapping["id"] = obj.external_id
        mapping["patient"] = PatientListSpec.serialize(obj.patient).to_json()


class EncounterRetrieveSpec(EncounterListSpec):
    appointment: dict = {}

    @classmethod
    def perform_extra_serialization(cls, mapping, obj):
        super().perform_extra_serialization(mapping, obj)
        if obj.appointment:
            mapping["appointment"] = TokenBookingReadSpec.serialize(
                obj.appointment
            ).to_json()
        if obj.created_by:
            mapping["created_by"] = UserSpec.serialize(obj.created_by)
        if obj.updated_by:
            mapping["updated_by"] = UserSpec.serialize(obj.updated_by)
