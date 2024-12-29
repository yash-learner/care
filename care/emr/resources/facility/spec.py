from pydantic import UUID4

from care.emr.models import Organization
from care.emr.resources.base import EMRResource
from care.emr.resources.user.spec import UserSpec
from care.facility.models import (
    REVERSE_FACILITY_TYPES,
    REVERSE_REVERSE_FACILITY_TYPES,
    Facility,
)


class FacilityBareMinimumSpec(EMRResource):
    __model__ = Facility
    __exclude__ = ["geo_organization"]
    id: UUID4 | None = None
    name: str


class FacilityBaseSpec(FacilityBareMinimumSpec):
    description: str
    longitude: float
    latitude: float
    pincode: int
    address: str
    phone_number: str
    middleware_address: str | None = None
    facility_type: str


class FacilityCreateSpec(FacilityBaseSpec):
    geo_organization: UUID4
    features: list[int]

    def perform_extra_deserialization(self, is_update, obj):
        obj.geo_organization = Organization.objects.filter(
            external_id=self.geo_organization, org_type="govt"
        ).first()
        obj.facility_type = REVERSE_REVERSE_FACILITY_TYPES[self.facility_type]


class FacilityReadSpec(FacilityBaseSpec):
    features: list[int]
    cover_image_url: str

    @classmethod
    def perform_extra_serialization(cls, mapping, obj):
        mapping["id"] = obj.external_id

        if obj.created_by:
            mapping["created_by"] = UserSpec.serialize(obj.created_by)

        mapping["facility_type"] = REVERSE_FACILITY_TYPES[obj.facility_type]
