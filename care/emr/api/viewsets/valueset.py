from pydantic import BaseModel, Field
from rest_framework.decorators import action
from rest_framework.response import Response

from care.emr.api.viewsets.base import EMRBaseViewSet
from care.emr.fhir.resources.valueset import ValueSetResource
from care.emr.models.valueset import ValueSet
from care.emr.resources.valueset.spec import ValueSetSpec


class ExpandRequest(BaseModel):
    search: str = ""
    count: int = Field(10, gt=0, lt=100)


class ValueSetViewSet(EMRBaseViewSet):
    database_model = ValueSet
    pydantic_model = ValueSetSpec
    lookup_field = "slug"

    @action(detail=True, methods=["POST"])
    def expand(self, request, *args, **kwargs):
        request_params = ExpandRequest(**request.data)
        obj = self.pydantic_model.serialize(self.get_object())
        results = (
            ValueSetResource()
            .filter(
                **request_params.model_dump(),
                **obj.compose.model_dump(exclude_defaults=True),
            )
            .search()
        )
        return Response({"results": [result.model_dump() for result in results]})
