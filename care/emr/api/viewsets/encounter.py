from django.db import transaction
from django_filters import rest_framework as filters
from rest_framework.exceptions import PermissionDenied
from rest_framework.generics import get_object_or_404

from care.emr.api.viewsets.base import (
    EMRBaseViewSet,
    EMRCreateMixin,
    EMRListMixin,
    EMRRetrieveMixin,
    EMRUpdateMixin,
)
from care.emr.models import Encounter, EncounterOrganization, FacilityOrganization
from care.emr.resources.encounter.constants import COMPLETED_CHOICES
from care.emr.resources.encounter.spec import (
    EncounterCreateSpec,
    EncounterListSpec,
    EncounterRetrieveSpec,
    EncounterUpdateSpec,
)
from care.facility.models import Facility
from care.security.authorization import AuthorizationController


class LiveFilter(filters.CharFilter):
    def filter(self, qs, value):
        queryset = qs
        if not value:
            return queryset
        if value.lower() == "true":
            queryset = queryset.filter(status__in=COMPLETED_CHOICES)
        elif value.lower() == "false":
            queryset = queryset.exclude(status__in=COMPLETED_CHOICES)
        return queryset


class EncounterFilters(filters.FilterSet):
    patient = filters.UUIDFilter(field_name="patient__external_id")
    facility = filters.UUIDFilter(field_name="facility__external_id")
    status = filters.CharFilter(field_name="status", lookup_expr="iexact")
    encounter_class = filters.CharFilter(
        field_name="encounter_class", lookup_expr="iexact"
    )
    priority = filters.CharFilter(field_name="priority", lookup_expr="iexact")
    external_identifier = filters.CharFilter(
        field_name="priority", lookup_expr="icontains"
    )
    live = LiveFilter()


class EncounterViewSet(
    EMRCreateMixin, EMRRetrieveMixin, EMRUpdateMixin, EMRListMixin, EMRBaseViewSet
):
    database_model = Encounter
    pydantic_model = EncounterCreateSpec
    pydantic_update_model = EncounterUpdateSpec
    pydantic_read_model = EncounterListSpec
    pydantic_retrieve_model = EncounterRetrieveSpec
    filterset_class = EncounterFilters
    filter_backends = [filters.DjangoFilterBackend]

    def get_facility_obj(self):
        return get_object_or_404(
            Facility, external_id=self.kwargs["facility_external_id"]
        )

    def perform_create(self, instance):
        with transaction.atomic():
            organizations = getattr(instance, "_organizations", [])
            super().perform_create(instance)
            for organization in organizations:
                EncounterOrganization.objects.create(
                    encounter=instance,
                    organization=FacilityOrganization.objects.get(
                        external_id=organization, facility=instance.facility
                    ),
                )
            if not organizations:
                instance.sync_organization_cache()

    def authorize_update(self, request_obj, model_instance):
        if not AuthorizationController.call(
            "can_create_encounter_obj", self.request.user, model_instance.facility
        ):
            raise PermissionDenied("You do not have permission to create encounter")

    def authorize_create(self, instance):
        # Check if encounter create permission exists on Facility Organization
        facility = get_object_or_404(Facility, external_id=instance.facility)
        if not AuthorizationController.call(
            "can_create_encounter_obj", self.request.user, facility
        ):
            raise PermissionDenied("You do not have permission to create encounter")

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .select_related("patient", "facility", "appointment")
            .order_by("-created_date")
        )
