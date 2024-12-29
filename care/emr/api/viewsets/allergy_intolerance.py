from django_filters import FilterSet, UUIDFilter
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework.exceptions import PermissionDenied

from care.emr.api.viewsets.authz_base import EncounterBasedAuthorizationBase
from care.emr.api.viewsets.base import EMRModelViewSet, EMRQuestionnaireResponseMixin
from care.emr.models import Encounter
from care.emr.models.allergy_intolerance import AllergyIntolerance
from care.emr.registries.system_questionnaire.system_questionnaire import (
    InternalQuestionnaireRegistry,
)
from care.emr.resources.allergy_intolerance.spec import (
    AllergyIntoleranceSpec,
    AllergyIntoleranceWriteSpec,
    AllergyIntrolanceSpecRead,
)
from care.emr.resources.questionnaire.spec import SubjectType
from care.security.authorization import AuthorizationController


class AllergyIntoleranceFilters(FilterSet):
    encounter = UUIDFilter(field_name="encounter__external_id")


@extend_schema_view(
    create=extend_schema(request=AllergyIntoleranceSpec),
)
class AllergyIntoleranceViewSet(
    EncounterBasedAuthorizationBase, EMRQuestionnaireResponseMixin, EMRModelViewSet
):
    database_model = AllergyIntolerance
    pydantic_model = AllergyIntoleranceSpec
    pydantic_read_model = AllergyIntrolanceSpecRead
    pydantic_update_model = AllergyIntoleranceWriteSpec
    questionnaire_type = "allergy_intolerance"
    questionnaire_title = "Allergy Intolerance"
    questionnaire_description = "Allergy Intolerance"
    questionnaire_subject_type = SubjectType.patient.value
    filterset_class = AllergyIntoleranceFilters
    filter_backends = [DjangoFilterBackend]

    def validate_data(self, instance: AllergyIntoleranceSpec, model_instance=None):
        if not model_instance:
            encounter = Encounter.objects.get(external_id=instance.encounter)
            if str(encounter.patient.external_id) != self.kwargs["patient_external_id"]:
                err = "Malformed request"
                raise PermissionDenied(err)

    def get_queryset(self):
        if not AuthorizationController.call(
            "can_view_clinical_data", self.request.user, self.get_patient_obj()
        ):
            raise PermissionDenied("Permission denied to user")
        return (
            super()
            .get_queryset()
            .filter(patient__external_id=self.kwargs["patient_external_id"])
            .select_related("patient", "encounter", "created_by", "updated_by")
            .order_by("-modified_date")
        )


InternalQuestionnaireRegistry.register(AllergyIntoleranceViewSet)
