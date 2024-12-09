from datetime import UTC, datetime
from enum import Enum

from pydantic import UUID4, BaseModel, Field, field_validator

from care.emr.fhir.schema.base import Annotation, Coding
from care.emr.models.service_request import ServiceRequest
from care.emr.models.specimen import Specimen
from care.emr.registries.care_valueset.care_valueset import validate_valueset
from care.emr.resources.base import EMRResource
from care.emr.resources.service_request.spec import ServiceRequestReadSpec
from care.emr.resources.specimen.valueset import (
    CARE_SPECIMEN_CONDITION_VALUESET,
    CARE_SPECIMEN_PROCESSING_METHOD_VALUESET,
    CARE_SPECIMEN_TYPE_VALUESET,
)
from care.facility.api.serializers.patient import PatientDetailSerializer
from care.users.api.serializers.user import UserBaseMinimumSerializer


class BaseSpecimenSpec(EMRResource):
    __model__ = Specimen
    __exclude__ = ["subject", "request"]
    id: UUID4 = None


class SpecimenProcessingSpec(EMRResource):
    description: str | None = Field(
        default=None,
        description="A description of the processing step",
    )
    method: Coding | None = Field(
        default=None,
        json_schema_extra={"slug": CARE_SPECIMEN_PROCESSING_METHOD_VALUESET.slug},
        description="The treatment/processing step applied to the specimen",
    )
    time: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="The datetime at which the processing step was performed",
    )
    performer: UUID4 | None = Field(
        default=None,
        description="References user who performed the processing step",
    )

    @field_validator("method")
    @classmethod
    def validate_method(cls, value: str):
        return validate_valueset(
            "method",
            cls.model_fields["method"].json_schema_extra["slug"],
            value,
        )


class StatusChoices(str, Enum):
    available = "available"
    unavailable = "unavailable"
    unsatisfactory = "unsatisfactory"
    entered_in_error = "entered-in-error"


class SpecimenSpec(BaseSpecimenSpec):
    identifier: str | None = Field(
        default=None,
        description="The unique identifier assigned to the specimen after collection",
    )
    accession_identifier: str | None = Field(
        default=None,
        description="The identifier assigned to the specimen by the laboratory",
    )

    status: StatusChoices | None = Field(
        default=None,
        description="Indicates the status of the specimen, used internally to track the lifecycle of the specimen, None indicates that the specimen is not yet collected",
    )

    type: Coding = Field(
        ...,
        json_schema_extra={"slug": CARE_SPECIMEN_TYPE_VALUESET.slug},
        description="Indicates the type of specimen being collected",
    )

    subject: UUID4 = Field(
        ...,
        description="The patient from whom the specimen is collected",
    )
    request: UUID4 = Field(
        ...,
        description="The service request that initiated the collection of the specimen",
    )

    collected_by: UUID4 | None = Field(
        default=None,
        description="References the user who collected the specimen",
    )
    collected_at: datetime | None = Field(
        default=None,
        description="The datetime at which the specimen was collected",
    )

    dispatched_by: UUID4 | None = Field(
        default=None,
        description="References the user who dispatched the specimen to the laboratory",
    )
    dispatched_at: datetime | None = Field(
        default=None,
        description="The datetime at which the specimen was dispatched to the laboratory",
    )

    received_by: UUID4 | None = Field(
        default=None,
        description="References the user who received the specimen at the laboratory",
    )
    received_at: datetime | None = Field(
        default=None,
        description="The datetime at which the specimen was received at the laboratory",
    )

    condition: Coding | None = Field(
        default=None,
        json_schema_extra={"slug": CARE_SPECIMEN_CONDITION_VALUESET.slug},
        description="The condition of the specimen while received at the laboratory",
    )

    processing: list[SpecimenProcessingSpec] = Field(
        default=[],
        description="The processing steps that have been performed on the specimen",
    )

    note: list[Annotation] = Field(
        default=[],
        description="Comments made about the service request by the requester, performer, subject, or other participants",
    )

    parent: UUID4 | None = Field(
        default=None,
        description="References the parent specimen from which this specimen was derived, used for aliquots and derived specimens",
    )

    @field_validator("type")
    @classmethod
    def validate_type(cls, value: str):
        return validate_valueset(
            "type", cls.model_fields["type"].json_schema_extra["slug"], value
        )

    @field_validator("condition")
    @classmethod
    def validate_condition(cls, value: str):
        return validate_valueset(
            "condition", cls.model_fields["condition"].json_schema_extra["slug"], value
        )

    def perform_extra_deserialization(self, is_update, obj):
        if not is_update:
            obj.request = ServiceRequest.objects.get(external_id=self.request)
            obj.subject = obj.request.subject


class SpecimenReadSpec(BaseSpecimenSpec):
    __exclude__ = []

    identifier: str | None
    accession_identifier: str | None

    status: StatusChoices | None

    type: Coding

    subject: dict
    request: ServiceRequestReadSpec

    collected_by: dict | None
    collected_at: datetime | None

    dispatched_by: dict | None
    dispatched_at: datetime | None

    received_by: dict | None
    received_at: datetime | None

    condition: Coding | None

    processing: list[SpecimenProcessingSpec]

    note: list[Annotation]

    parent: dict | None

    @classmethod
    def perform_extra_serialization(cls, mapping, obj):
        mapping["id"] = obj.external_id

        mapping["subject"] = PatientDetailSerializer(obj.subject).data

        mapping["collected_by"] = UserBaseMinimumSerializer(obj.collected_by).data
        mapping["dispatched_by"] = UserBaseMinimumSerializer(obj.dispatched_by).data
        mapping["received_by"] = UserBaseMinimumSerializer(obj.received_by).data

        mapping["parent"] = (
            SpecimenReadSpec().serialize(obj.parent).model_dump(exclude=["meta"])
            if obj.parent
            else None
        )


class SpecimenCollectRequest(BaseModel):
    identifier: str | None = Field(
        default=None,
        description="The identifier assigned to the specimen while collecting, this can be barcode or any other identifier",
    )


class SpecimenSendToLabRequest(BaseModel):
    lab: UUID4 = Field(
        ...,
        description="The laboratory to which the specimen is being sent",
    )


class SpecimenReceiveAtLabRequest(BaseModel):
    accession_identifier: str | None = Field(
        default=None,
        description="The identifier assigned to the specimen by the laboratory",
    )

    condition: Coding | None = Field(
        default=None,
        description="The condition of the specimen while received at the laboratory",
    )

    note: Annotation = Field(
        default=None,
        description="Comments made about the specimen while received at the laboratory",
    )

    @field_validator("condition")
    @classmethod
    def validate_condition(cls, value: str):
        return validate_valueset(
            "condition",
            SpecimenSpec.model_fields["condition"].json_schema_extra["slug"],
            value,
        )


class SpecimenProcessRequest(BaseModel):
    process: list[SpecimenProcessingSpec] = Field(
        ...,
        description="The processing steps that have been performed on the specimen",
    )
