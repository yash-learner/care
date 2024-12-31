from rest_framework.exceptions import PermissionDenied
from rest_framework.generics import get_object_or_404

from care.emr.api.viewsets.authz_base import EncounterBasedAuthorizationBase
from care.emr.api.viewsets.base import (
    EMRBaseViewSet,
    EMRCreateMixin,
    EMRListMixin,
    EMRRetrieveMixin,
    EMRUpdateMixin,
)
from care.emr.models.notes import NoteMessage, NoteThread
from care.emr.models.patient import Patient
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
from care.security.authorization import AuthorizationController


class NoteThreadViewSet(
    EncounterBasedAuthorizationBase,
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
            Patient, external_id=self.kwargs["patient_external_id"]
        )

    def authorize_create(self, instance):
        pass

    def authorize_update(self, request_obj, model_instance):
        pass

    def authorize_delete(self, instance):
        pass

    def perform_create(self, instance):
        instance.patient = self.get_patient()
        if instance.encounter and instance.encounter.patient != instance.patient:
            raise ValueError("Patient Mismatch")
        super().perform_create(instance)

    def get_object(self):
        # TODO Authorise Based on encounter and permission
        return super().get_object()

    def get_queryset(self):
        if not AuthorizationController.call(
            "can_view_clinical_data", self.request.user, self.get_patient_obj()
        ):
            raise PermissionDenied("Permission denied to user")
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

        return queryset.order_by("-created_date")


class NoteMessageViewSet(
    EMRCreateMixin, EMRRetrieveMixin, EMRUpdateMixin, EMRListMixin, EMRBaseViewSet
):
    database_model = NoteMessage
    pydantic_model = NoteMessageCreateSpec
    pydantic_read_model = NoteMessageReadSpec
    pydantic_update_model = NoteMessageUpdateSpec

    # TODO Authorise Based on encounter and patient

    def get_patient_obj(self):
        return get_object_or_404(
            Patient, external_id=self.kwargs["patient_external_id"]
        )

    def perform_create(self, instance):
        instance.thread = get_object_or_404(
            NoteThread, external_id=self.kwargs["thread_external_id"]
        )
        super().perform_create(instance)

    def authorize_update(self, request_obj, model_instance):
        if self.request.user != model_instance.created_by:
            raise PermissionDenied("Cannot Update Message Created by Other User")

        if not AuthorizationController.call(
            "can_update_encounter_obj",
            self.request.user,
            model_instance.thread.encounter,
        ):
            raise PermissionDenied("You do not have permission to update encounter")

    def authorize_create(self, instance):
        thread = get_object_or_404(
            NoteThread, external_id=self.kwargs["thread_external_id"]
        )
        if not AuthorizationController.call(
            "can_update_encounter_obj", self.request.user, thread.encounter
        ):
            raise PermissionDenied("You do not have permission to update encounter")

    def authorize_delete(self, instance):
        if not AuthorizationController.call(
            "can_update_encounter_obj", self.request.user, instance.encounter
        ):
            raise PermissionDenied("You do not have permission to update encounter")

    def get_queryset(self):
        if not AuthorizationController.call(
            "can_view_clinical_data", self.request.user, self.get_patient_obj()
        ):
            raise PermissionDenied("Permission denied to user")
        return (
            super()
            .get_queryset()
            .filter(thread__external_id=self.kwargs["thread_external_id"])
            .order_by("-created_date")
        )
