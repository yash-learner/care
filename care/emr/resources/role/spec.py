from pydantic import UUID4, BaseModel

from care.emr.resources.base import EMRResource
from care.security.models import RoleModel


class PermissionSpec(BaseModel):
    name: str
    description: str
    slug: str
    context: str


class RoleSpec(EMRResource):
    __model__ = RoleModel
    __exclude__ = ["permissions"]

    id: UUID4
    name: str
    description: str
    is_system: bool
    permissions: list[PermissionSpec]

    @classmethod
    def perform_extra_serialization(cls, mapping, obj):
        mapping["id"] = obj.external_id
        mapping["permissions"] = obj.get_permissions_for_role()
        return mapping
