from datetime import datetime
from enum import Enum

from pydantic import UUID4, BaseModel, Field, field_validator

from care.emr.fhir.schema.base import Coding, Quantity
from care.emr.models.medication_administration import MedicationAdministration
from care.emr.models.medication_request import MedicationRequest
from care.emr.resources.base import EMRResource
from care.emr.resources.medication.valueset.administration_method import (
    CARE_ADMINISTRATION_METHOD_VALUESET,
)
from care.emr.resources.medication.valueset.body_site import CARE_BODY_SITE_VALUESET
from care.emr.resources.medication.valueset.medication import CARE_MEDICATION_VALUESET
from care.emr.resources.medication.valueset.route import CARE_ROUTE_VALUESET
from care.emr.resources.user.spec import UserSpec
from care.facility.models.patient_consultation import PatientConsultation


class MedicationAdministrationStatus(str, Enum):
    completed = "completed"
    not_done = "not_done"
    entered_in_error = "entered_in_error"
    stopped = "stopped"
    in_progress = "in_progress"
    on_hold = "on_hold"
    unknown = "unknown"
    cancelled = "cancelled"


class MedicationAdministrationCategory(str, Enum):
    inpatient = "inpatient"
    outpatient = "outpatient"
    community = "community"
    discharge = "discharge"


class MedicationAdministrationPerformerFunction(str, Enum):
    performer = "performer"
    verifier = "verifier"
    witness = "witness"


class MedicationAdministrationPerformer(BaseModel):
    actor: UUID4 = Field(
        ...,
        description="Who or what performed the administration",
    )
    function: MedicationAdministrationPerformerFunction | None = Field(
        ...,
        description="The function of the performer",
    )


class Dosage(BaseModel):
    text: str | None = Field(
        None,
        description="Free text dosage instructions",
    )
    site: Coding | None = Field(
        None,
        description="The site of the administration",
        json_schema_extra={"slug": CARE_BODY_SITE_VALUESET.slug},
    )
    route: Coding | None = Field(
        None,
        description="The route of the administration",
        json_schema_extra={"slug": CARE_ROUTE_VALUESET.slug},
    )
    method: Coding | None = Field(
        None,
        description="The method of the administration",
        json_schema_extra={"slug": CARE_ADMINISTRATION_METHOD_VALUESET.slug},
    )
    dose: Quantity | None = Field(
        None,
        description="The amount of medication administered",
    )
    rate: Quantity | None = Field(
        None,
        description="The speed of administration",
    )


class BaseMedicationAdministrationSpec(EMRResource):
    __model__ = MedicationAdministration
    __exclude__ = ["patient", "encounter", "request"]
    id: UUID4 = None

    status: MedicationAdministrationStatus = Field(
        ...,
        description="Represents the current status of the medication administration",
    )
    status_reason: Coding | None = Field(
        None,
        description="The reason why the medication was not administered",
        json_schema_extra={"slug": CARE_MEDICATION_VALUESET.slug},
    )
    category: MedicationAdministrationCategory | None = Field(
        None,
        description="The category of the medication administration",
    )

    medication: Coding = Field(
        ...,
        description="The medication that was taken",
        json_schema_extra={"slug": CARE_MEDICATION_VALUESET.slug},
    )

    authored_on: datetime | None = Field(
        None,
        description="When request was initially authored",
    )
    occurrence_period_start: datetime = Field(
        description="When the medication was administration started",
    )
    occurrence_period_end: datetime | None = Field(
        None,
        description="When the medication administration ended. If not provided, it is assumed to be ongoing",
    )
    recorded: datetime | None = Field(
        None,
        description="When administration was recorded",
    )

    encounter: UUID4 = Field(
        ...,
        description="The encounter where the administration was noted",
    )
    request: UUID4 = Field(
        ...,
        description="The medication request under which the administration was made",
    )

    performer: list[MedicationAdministrationPerformer] | None = Field(
        None,
        description="Who administered the medication",
    )
    dosage: Dosage | None = Field(
        None,
        description="The dosage of the medication",
    )

    note: str | None = Field(
        None,
        description="Any additional notes about the medication",
    )


class MedicationAdministrationSpec(BaseMedicationAdministrationSpec):
    @field_validator("encounter")
    @classmethod
    def validate_encounter_exists(cls, encounter):
        if not PatientConsultation.objects.filter(external_id=encounter).exists():
            err = "Encounter not found"
            raise ValueError(err)
        return encounter

    @field_validator("request")
    @classmethod
    def validate_request(cls, request):
        if not MedicationRequest.objects.filter(external_id=request).exists():
            err = "Medication Request not found"
            raise ValueError(err)
        return request

    def perform_extra_deserialization(self, is_update, obj):
        if not is_update:
            obj.encounter = PatientConsultation.objects.get(
                external_id=self.encounter
            )  # Needs more validation
            obj.patient = obj.encounter.patient
            obj.request = MedicationRequest.objects.get(external_id=self.request)


class MedicationAdministrationReadSpec(BaseMedicationAdministrationSpec):
    created_by: UserSpec = dict
    updated_by: UserSpec = dict

    @classmethod
    def perform_extra_serialization(cls, mapping, obj):
        mapping["id"] = obj.external_id
        mapping["encounter"] = obj.encounter.external_id
        mapping["request"] = obj.request.external_id

        if obj.created_by:
            mapping["created_by"] = UserSpec.serialize(obj.created_by)
        if obj.updated_by:
            mapping["updated_by"] = UserSpec.serialize(obj.updated_by)
