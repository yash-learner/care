from enum import Enum

from django.core.validators import slug_re
from pydantic import UUID4, Field, field_validator, model_validator

from care.emr.fhir.schema.valueset.valueset import ValueSetCompose
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
    slug: str | None = Field(None, min_length=5, max_length=25, pattern=r"^[-\w]+$")
    name: str
    description: str
    compose: ValueSetCompose
    status: ValueSetStatusOptions
    is_system_defined: bool = False

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, slug: str) -> str:
        if not slug_re.match(slug):
            err = "Slug must be alphanumeric and can contain hyphens, underscores, and periods."
            raise ValueError(err)
        return slug

    @model_validator(mode="after")
    def validate_slug_system(self):
        if not self.is_system_defined and "system-" in self.slug:
            err = "Cannot create valueset with system like slug"
            raise ValueError(err)
        return self

    def perform_extra_deserialization(self, is_update, obj):
        obj.compose = self.compose.model_dump(exclude_defaults=True, exclude_none=True)


ValueSetSpec.model_rebuild()
