from drf_spectacular.utils import extend_schema, extend_schema_view

from care.emr.api.viewsets.base import EMRModelViewSet
from care.emr.models.specimen import Specimen
from care.emr.resources.specimen.spec import SpecimenReadSpec, SpecimenSpec


@extend_schema_view(
    create=extend_schema(request=SpecimenSpec),
)
class SpecimenViewSet(EMRModelViewSet):
    database_model = Specimen
    pydantic_model = SpecimenSpec
    pydantic_read_model = SpecimenReadSpec
