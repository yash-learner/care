import datetime

from django_filters import CharFilter, FilterSet
from django_filters.rest_framework import DjangoFilterBackend
from pydantic import BaseModel
from rest_framework.decorators import action
from rest_framework.response import Response

from care.emr.api.viewsets.base import EMRModelViewSet
from care.emr.models.patient import Patient
from care.emr.resources.patient.spec import (
    PatientCreateSpec,
    PatientListSpec,
    PatientRetrieveSpec,
)
from care.security.authorization import AuthorizationController


class PatientFilters(FilterSet):
    name = CharFilter(field_name="name", lookup_expr="icontains")
    phone_number = CharFilter(field_name="phone_number", lookup_expr="iexact")


class PatientViewSet(EMRModelViewSet):
    database_model = Patient
    pydantic_model = PatientCreateSpec
    pydantic_read_model = PatientListSpec
    pydantic_retrieve_model = PatientRetrieveSpec
    filterset_class = PatientFilters
    filter_backends = [DjangoFilterBackend]

    # TODO : Retrieve will work if an active encounter exists on the patient

    def get_queryset(self):
        qs = (
            super()
            .get_queryset()
            .select_related("created_by", "updated_by", "geo_organization")
        )
        return AuthorizationController.call(
            "get_filtered_patients", qs, self.request.user
        )

    class SearchRequestSpec(BaseModel):
        name: str
        phone_number: str
        date_of_birth: datetime.date | None = None
        year_of_birth: int

    @action(detail=False, methods=["POST"])
    def search(self, request, *args, **kwargs):
        max_page_size = 200
        request_data = self.SearchRequestSpec(**request.data)
        search_filters = {
            "year_of_birth": request_data.year_of_birth,
            "phone_number": request_data.phone_number,
        }
        if request_data.date_of_birth:
            search_filters["date_of_birth"] = request_data.date_of_birth
        queryset = Patient.objects.filter(**search_filters)
        if request_data.name:
            queryset = (queryset.filter(name__icontains=request_data.name))[
                :max_page_size
            ]
        data = [
            self.get_read_pydantic_model().serialize(obj).to_json() for obj in queryset
        ]
        return Response({"results": data})
