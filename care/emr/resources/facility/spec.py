from pydantic import UUID4

from care.emr.resources.base import EMRResource
from care.facility.models import Facility


class FacilityBareMinimumSpec(EMRResource):
    __model__ = Facility

    id: UUID4
    name: str
