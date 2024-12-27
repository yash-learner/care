from rest_framework.exceptions import PermissionDenied
from rest_framework.generics import get_object_or_404

from care.emr.api.viewsets.base import (
    EMRBaseViewSet,
    EMRCreateMixin,
    EMRListMixin,
    EMRRetrieveMixin,
    EMRUpdateMixin,
)
from care.emr.models.notes import NoteMessage, NoteThread
from care.emr.resources.notes.notes_spec import (
    NoteMessageCreateSpec,
    NoteMessageReadSpec,
    NoteMessageUpdateSpec,
)
from care.emr.resources.notes.thread_spec import (
    NoteThreadCreateSpec,
    NoteThreadReadSpec,
    NoteThreadUpdateSpec,
)
from care.facility.models import PatientRegistration


class NoteThreadViewSet(
    EMRCreateMixin,
    EMRRetrieveMixin,
    EMRUpdateMixin,
    EMRListMixin,
    EMRBaseViewSet,
):
    database_model = NoteThread
    pydantic_model = NoteThreadCreateSpec
    pydantic_read_model = NoteThreadUpdateSpec
    pydantic_update_model = NoteThreadReadSpec

    def get_patient(self):
        return get_object_or_404(
            PatientRegistration, external_id=self.kwargs["patient_external_id"]
        )

    def perform_create(self, instance):
        instance.patient = self.get_patient()
        if instance.encounter and instance.encounter.patient != instance.patient:
            raise ValueError("Patient Mismatch")
        super().perform_create(instance)

    def get_object(self):
        # TODO Authorise Based on encounter and permission
        return super().get_object()

    def get_queryset(self):
        queryset = (
            super()
            .get_queryset()
            .filter(patient__external_id=self.kwargs["patient_external_id"])
        )

        encounter = self.request.GET.get("encounter", None)
        if encounter and self.action == "list":
            # TODO Authorise Encounter
            queryset = queryset.filter(encounter__external_id=encounter)
        else:
            # TODO Authorise Patient
            queryset = queryset.filter(encounter__isnull=True)

        return (
            super()
            .get_queryset()
            .filter(patient__external_id=self.kwargs["patient_external_id"])
        )


class NoteMessageViewSet(
    EMRCreateMixin, EMRRetrieveMixin, EMRUpdateMixin, EMRListMixin, EMRBaseViewSet
):
    database_model = NoteMessage
    pydantic_model = NoteMessageCreateSpec
    pydantic_read_model = NoteMessageReadSpec
    pydantic_update_model = NoteMessageUpdateSpec

    # TODO Authorise Based on encounter and patient

    def perform_create(self, instance):
        instance.thread = get_object_or_404(
            NoteThread, external_id=self.kwargs["thread_external_id"]
        )
        super().perform_create(instance)

    def authorize_update(self, request_obj, model_instance):
        if self.request.user != model_instance.created_by:
            raise PermissionDenied("Cannot Update Message Created by Other User")

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .filter(thread__external_id=self.kwargs["thread_external_id"])
        )
