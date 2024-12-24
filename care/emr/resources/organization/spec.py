from enum import Enum

from pydantic import UUID4, model_validator

from care.emr.models.organziation import Organization
from care.emr.resources.base import EMRResource
from care.emr.resources.user.spec import UserSpec


class OrganizationTypeChoices(str, Enum):
    team = "team"
    govt = "govt"
    role = "role"
    other = "other"


class OrganizationBaseSpec(EMRResource):
    __model__ = Organization
    __exclude__ = ["parent"]
    id: str = None
    active: bool = True
    org_type: OrganizationTypeChoices
    name: str
    description: str = ""
    parent: UUID4 | None = None


class OrganizationWriteSpec(OrganizationBaseSpec):
    @model_validator(mode="after")
    def validate_parent_organization(self):
        if (
            self.parent
            and not Organization.objects.filter(external_id=self.parent).exists()
        ):
            err = "Parent not found"
            raise ValueError(err)
        return self

    def perform_extra_deserialization(self, is_update, obj):
        if not is_update:
            if self.parent:
                obj.parent = Organization.objects.get(external_id=self.parent)
                obj.level_cache = obj.parent.level_cache + 1
                obj.parent_cache = [*obj.parent.parent_cache, obj.parent.id]
                if obj.parent.root_org is None:
                    obj.root_org = obj.parent
                else:
                    obj.root_org = obj.parent.root_org
            else:
                obj.parent = None


class OrganizationReadSpec(OrganizationBaseSpec):
    created_by: UserSpec = dict
    updated_by: UserSpec = dict
    level_cache: int = 0
    system_generated: bool

    @classmethod
    def perform_extra_serialization(cls, mapping, obj):
        mapping["id"] = obj.external_id
        mapping["parent"] = obj.parent.external_id if obj.parent else None

        if obj.created_by:
            mapping["created_by"] = UserSpec.serialize(obj.created_by)
        if obj.updated_by:
            mapping["updated_by"] = UserSpec.serialize(obj.updated_by)
