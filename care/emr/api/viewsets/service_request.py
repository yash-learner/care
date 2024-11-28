from drf_spectacular.utils import extend_schema, extend_schema_view

from care.emr.api.viewsets.base import EMRModelViewSet
from care.emr.models.service_request import ServiceRequest
from care.emr.resources.service_request.spec import (
    ServiceRequestReadSpec,
    ServiceRequestSpec,
)


@extend_schema_view(
    create=extend_schema(request=ServiceRequestSpec),
)
class ServiceRequestViewSet(EMRModelViewSet):
    database_model = ServiceRequest
    pydantic_model = ServiceRequestSpec
    pydantic_read_model = ServiceRequestReadSpec

    def clean_create_data(self, request, *args, **kwargs):
        clean_data = super().clean_create_data(request, *args, **kwargs)

        clean_data["requester"] = request.user.external_id
        return clean_data
