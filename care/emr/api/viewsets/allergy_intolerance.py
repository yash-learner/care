from django_filters import FilterSet, UUIDFilter
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework.exceptions import PermissionDenied

from care.emr.api.viewsets.base import EMRModelViewSet
from care.emr.models.allergy_intolerance import AllergyIntolerance
from care.emr.registries.system_questionnaire.system_questionnaire import (
    InternalQuestionnaireRegistry,
)
from care.emr.resources.allergy_intolerance.spec import (
    AllergyIntoleranceSpec,
    AllergyIntrolanceSpecRead,
)
from care.emr.resources.questionnaire.spec import SubjectType
from care.facility.models.patient_consultation import PatientConsultation


class AllergyIntoleranceFilters(FilterSet):
    encounter = UUIDFilter(field_name="encounter__external_id")


@extend_schema_view(
    create=extend_schema(request=AllergyIntoleranceSpec),
)
class AllergyIntoleranceViewSet(EMRModelViewSet):
    database_model = AllergyIntolerance
    pydantic_model = AllergyIntoleranceSpec
    pydantic_read_model = AllergyIntrolanceSpecRead
    questionnaire_type = "allergy_intolerance"
    questionnaire_title = "Allergy Intolerance"
    questionnaire_description = "Allergy Intolerance"
    questionnaire_subject_type = SubjectType.patient.value
    filterset_class = AllergyIntoleranceFilters
    filter_backends = [DjangoFilterBackend]

    def authorize_create(self, request, request_model: AllergyIntoleranceSpec):
        encounter = PatientConsultation.objects.get(external_id=request_model.encounter)
        if str(encounter.patient.external_id) != self.kwargs["patient_external_id"]:
            err = "Malformed request"
            raise PermissionDenied(err)
        # Check if the user has access to the patient and write access to the encounter

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .filter(patient__external_id=self.kwargs["patient_external_id"])
            .select_related("patient", "encounter")
        )


InternalQuestionnaireRegistry.register(AllergyIntoleranceViewSet)
