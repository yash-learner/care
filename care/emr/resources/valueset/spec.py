from enum import Enum

from pydantic import UUID4

from care.emr.fhir.schema.valueset.valueset import (
    ValueSetCompose,
)
from care.emr.models.valueset import ValueSet as ValuesetDatabaseModel
from care.emr.resources.base import EMRResource


class ValueSetStatusOptions(str, Enum):
    draft = "draft"
    active = "active"
    retired = "retired"
    unknown = "unknown"


class ValueSetSpec(EMRResource):
    __model__ = ValuesetDatabaseModel

    id: UUID4 = None
    slug: str
    name: str
    description: str
    compose: ValueSetCompose
    status: ValueSetStatusOptions
    is_system_defined: bool = False

    def perform_extra_deserialization(self, is_update, obj):
        obj.compose = self.compose.model_dump(exclude_defaults=True, exclude_none=True)


ValueSetSpec.model_rebuild()
