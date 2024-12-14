import json

from django.db import transaction
from django.http.response import Http404
from pydantic import ValidationError
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError as RestFrameworkValidationError
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler
from rest_framework.viewsets import GenericViewSet

from care.emr.models import QuestionnaireResponse
from care.emr.models.base import EMRBaseModel
from care.emr.resources.base import EMRResource


def emr_exception_handler(exc, context):
    if isinstance(exc, ValidationError):
        return Response({"errors": json.loads(exc.json())}, status=400)
    if isinstance(exc, Http404):
        return Response(
            {
                "errors": [
                    {
                        "type": "object_not_found",
                        "msg": "Object not found",
                    }
                ]
            },
            status=404,
        )
    if isinstance(exc, RestFrameworkValidationError) and getattr(exc, "detail", None):
        return Response({"errors": [exc.detail]}, status=400)
    return drf_exception_handler(exc, context)


class EMRQuestionnaireMixin:
    @action(detail=False, methods=["GET"])
    def questionnaire_spec(self, *args, **kwargs):
        return Response(
            {"version": "1.0", "questions": self.pydantic_model.questionnaire()}
        )

    @action(detail=False, methods=["GET"])
    def json_schema_spec(self, *args, **kwargs):
        return Response(
            {"version": "1.0", "questions": self.pydantic_model.model_json_schema()}
        )


class EMRRetrieveMixin:
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        data = self.get_read_pydantic_model().serialize(instance)
        return Response(data.model_dump(exclude=["meta"]))


class EMRCreateMixin:
    CREATE_QUESTIONNAIRE_RESPONSE = True

    def perform_create(self, instance):
        instance.created_by = self.request.user
        instance.updated_by = self.request.user
        with transaction.atomic():
            instance.save()
            if self.CREATE_QUESTIONNAIRE_RESPONSE:
                QuestionnaireResponse.objects.create(
                    subject_id=self.fetch_patient_from_instance(instance).external_id,
                    patient=self.fetch_patient_from_instance(instance),
                    encounter=self.fetch_encounter_from_instance(instance),
                    structured_responses={
                        self.questionnaire_type: {
                            "submit_type": "CREATE",
                            "id": str(instance.external_id),
                        }
                    },
                    structured_response_type=self.questionnaire_type,
                    created_by=self.request.user,
                    updated_by=self.request.user,
                )

    def clean_create_data(self, request_data):
        return request_data

    def authorize_create(self, request_user, request_instance):
        pass

    def create(self, request, *args, **kwargs):
        return Response(self.handle_create(request.data, request.user))

    def handle_create(self, request_data, request_user):
        clean_data = self.clean_create_data(request_data)
        instance = self.pydantic_model(**clean_data)
        self.authorize_create(request_user, instance)
        model_instance = instance.de_serialize()
        self.perform_create(model_instance)
        return (
            self.get_read_pydantic_model()
            .serialize(model_instance)
            .model_dump(exclude=["meta"])
        )


class EMRListMixin:
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request)
        if page is not None:
            data = [
                self.get_read_pydantic_model()
                .serialize(obj)
                .model_dump(exclude=["meta"])
                for obj in page
            ]
            return paginator.get_paginated_response(data)
        data = [
            self.get_read_pydantic_model().serialize(obj).model_dump(exclude=["meta"])
            for obj in queryset
        ]
        return Response(data)


class EMRUpdateMixin:
    def perform_update(self, instance):
        instance.updated_by = self.request.user
        # TODO Handle hisorical data by taking a dump from current model and appending to history object
        with transaction.atomic():
            instance.save()
            if self.CREATE_QUESTIONNAIRE_RESPONSE:
                QuestionnaireResponse.objects.create(
                    subject_id=self.fetch_patient_from_instance(instance),
                    patient=self.fetch_patient_from_instance(instance),
                    encounter=self.fetch_encounter_from_instance(instance),
                    structured_responses={
                        self.questionnaire_type: {
                            "submit_type": "UPDATE",
                            "id": str(instance.external_id),
                        }
                    },
                    structured_response_type=self.questionnaire_type,
                    created_by=self.request.user,
                    updated_by=self.request.user,
                )

    def clean_update_data(self, request_data):
        request_data.pop("id", None)
        request_data.pop("external_id", None)
        request_data.pop("patient", None)
        request_data.pop("encounter", None)
        return request_data

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        return Response(self.handle_update(instance, request.data, request.user))

    def handle_update(self, instance, request_data, request_user):
        clean_data = self.clean_update_data(request_data)  # From Create
        pydantic_model = self.get_update_pydantic_model()
        serializer_obj = pydantic_model.model_validate(
            clean_data, context={"is_update": True, "object": instance}
        )
        model_instance = serializer_obj.de_serialize(obj=instance)
        self.perform_update(model_instance)
        return (
            self.get_read_pydantic_model()
            .serialize(model_instance)
            .model_dump(exclude=["meta"])
        )


class EMRDeleteMixin:
    def perform_delete(self, instance):
        instance.deleted = True
        instance.save(update_fields=["deleted"])

    def delete(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_delete(instance)
        return Response(status=204)


class EMRUpsertMixin:
    @action(detail=False, methods=["POST"])
    def upsert(self, request, *args, **kwargs):
        datapoints = request.data.get("datapoints", [])
        results = []
        errored = False
        try:
            with transaction.atomic():
                for datapoint in datapoints:
                    try:
                        if "id" in datapoint:
                            instance = get_object_or_404(
                                self.database_model, external_id=datapoint["id"]
                            )
                            result = self.handle_update(
                                instance, datapoint, request.user
                            )
                        else:
                            result = self.handle_create(datapoint, request.user)
                        results.append(result)
                    except Exception as e:
                        errored = True
                        results.append(emr_exception_handler(e, {}).data)
                if errored:
                    raise Exception
        except Exception:
            return Response(results, status=400)
        return Response(results)


class EMRBaseViewSet(GenericViewSet):
    pydantic_model: EMRResource = None
    pydantic_read_model: EMRResource = None
    pydantic_update_model: EMRResource = None
    database_model: EMRBaseModel = None
    lookup_field = "external_id"

    def get_exception_handler(self):
        return emr_exception_handler

    def get_queryset(self):
        return self.filter_queryset(self.database_model.objects.all())

    def get_read_pydantic_model(self):
        if self.pydantic_read_model:
            return self.pydantic_read_model
        return self.pydantic_model

    def get_update_pydantic_model(self):
        if self.pydantic_update_model:
            return self.pydantic_update_model
        return self.pydantic_model

    def get_object(self):
        queryset = self.get_queryset()
        return get_object_or_404(
            queryset, **{self.lookup_field: self.kwargs[self.lookup_field]}
        )

    def fetch_encounter_from_instance(self, instance):
        return instance.encounter

    def fetch_patient_from_instance(self, instance):
        return instance.patient


class EMRModelViewSet(
    EMRCreateMixin,
    EMRRetrieveMixin,
    EMRUpdateMixin,
    EMRListMixin,
    EMRDeleteMixin,
    EMRQuestionnaireMixin,
    EMRBaseViewSet,
    EMRUpsertMixin,
):
    pass


class EMRModelReadOnlyViewSet(
    EMRRetrieveMixin,
    EMRListMixin,
    EMRQuestionnaireMixin,
    EMRBaseViewSet,
):
    pass
