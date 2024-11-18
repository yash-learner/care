from drf_spectacular.utils import extend_schema
from pydantic import BaseModel, Field
from rest_framework.decorators import action
from rest_framework.response import Response

from care.emr.api.viewsets.base import EMRBaseViewSet
from care.emr.fhir.schema.base import Coding
from care.emr.models.valueset import ValueSet
from care.emr.resources.valueset.spec import ValueSetSpec


class ExpandRequest(BaseModel):
    search: str = ""
    count: int = Field(10, gt=0, lt=100)


class LookupRequest(BaseModel):
    code: Coding


class ValueSetViewSet(EMRBaseViewSet):
    database_model = ValueSet
    pydantic_model = ValueSetSpec
    lookup_field = "slug"

    def get_serializer_class(self):
        return ValueSetSpec

    @extend_schema(request=ExpandRequest, responses={200: None}, methods=["POST"])
    @action(detail=True, methods=["POST"])
    def expand(self, request, *args, **kwargs):
        request_params = ExpandRequest(**request.data)
        results = self.get_object().search(**request_params.model_dump())
        return Response({"results": [result.model_dump() for result in results]})

    @extend_schema(request=LookupRequest, responses={200: None}, methods=["POST"])
    @action(detail=True, methods=["POST"])
    def lookup(self, request, *args, **kwargs):
        request_params = LookupRequest(**request.data)
        result = self.get_object().lookup(request_params.code)
        return Response({"result": result})
