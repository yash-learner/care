from datetime import datetime
from enum import Enum

from pydantic import UUID4, Field, field_validator

from care.emr.fhir.schema.base import Annotation, Coding
from care.emr.models.service_request import ServiceRequest
from care.emr.models.specimen import Specimen
from care.emr.registries.care_valueset.care_valueset import validate_valueset
from care.emr.resources.base import EMRResource
from care.emr.resources.specimen.valueset import (
    CARE_SPECIMEN_PROCESSING_METHOD_VALUESET,
    CARE_SPECIMEN_TYPE_VALUESET,
)


class BaseSpecimenSpec(EMRResource):
    __model__ = Specimen
    __exclude__ = ["subject", "request"]
    id: UUID4 = None


class SpecimenProcessingSpec(EMRResource):
    description: str | None = Field(
        default=None,
        description="A description of the processing step",
    )
    method: Coding = Field(
        ...,
        json_schema_extra={"slug": CARE_SPECIMEN_PROCESSING_METHOD_VALUESET.slug},
        description="The treatment/processing step applied to the specimen",
    )
    time: datetime = Field(
        ...,
        description="The datetime at which the processing step was performed",
    )
    performer: UUID4 = Field(
        ...,
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

    processing: list[SpecimenProcessingSpec] = Field(
        default=[],
        description="The processing steps that have been performed on the specimen",
    )

    note: list[Annotation] = Field(
        default=[],
        description="Comments made about the service request by the requester, performer, subject, or other participants",
    )

    @field_validator("type")
    @classmethod
    def validate_type(cls, value: str):
        return validate_valueset(
            "type", cls.model_fields["type"].json_schema_extra["slug"], value
        )

    def perform_extra_deserialization(self, is_update, obj):
        if not is_update:
            obj.request = ServiceRequest.objects.get(external_id=self.request)
            obj.subject = obj.request.subject


class SpecimenReadSpec(BaseSpecimenSpec):
    accession_identifier: str | None

    status: str | None

    type: Coding

    collected_at: datetime | None

    processing: list[SpecimenProcessingSpec]

    note: list[Annotation]
