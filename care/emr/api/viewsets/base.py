import json

from pydantic import ValidationError
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler
from rest_framework.viewsets import GenericViewSet

from care.emr.models.base import EMRBaseModel
from care.emr.resources.base import EMRResource


def emr_exception_handler(exc, context):
    if isinstance(exc, ValidationError):
        return Response({"errors": json.loads(exc.json())}, status=400)
    return drf_exception_handler(exc, context)


class EMRQuestionnaireMixin:
    @action(detail=False, methods=["GET"])
    def questionnaire_spec(self, *args, **kwargs):
        return Response(
            {"version": 1, "questions": self.pydantic_model.questionnaire()}
        )

    @action(detail=False, methods=["GET"])
    def json_schema_spec(self, *args, **kwargs):
        return Response(
            {"version": 1, "questions": self.pydantic_model.model_json_schema()}
        )


class EMRRetrieveMixin:
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        data = self.get_read_pydantic_model().serialize(instance)
        return Response(data.model_dump(exclude=["meta"]))


class EMRCreateMixin:
    def perform_create(self, instance):
        instance.save()

    def clean_create_data(self, request, *args, **kwargs):
        return request.data

    def create(self, request, *args, **kwargs):
        clean_data = self.clean_create_data(request, *args, **kwargs)
        instance = self.pydantic_model(**clean_data)
        model_instance = instance.de_serialize()
        self.perform_create(model_instance)
        return Response(
            self.get_read_pydantic_model()
            .serialize(model_instance)
            .model_dump(exclude=["meta"])
        )


class EMRListMixin:
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
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


class EMRBaseViewSet(GenericViewSet):
    pydantic_model: EMRResource = None
    pydantic_read_model: EMRResource = None
    database_model: EMRBaseModel = None
    lookup_field = "external_id"

    def get_exception_handler(self):
        return emr_exception_handler

    def get_queryset(self):
        return self.database_model.objects.all()

    def get_read_pydantic_model(self):
        if self.pydantic_read_model:
            return self.pydantic_read_model
        return self.pydantic_model

    def get_object(self):
        queryset = self.get_queryset()
        return get_object_or_404(
            queryset, **{self.lookup_field: self.kwargs[self.lookup_field]}
        )

    def update(self, request, *args, **kwargs):
        return Response({"update": "working"})

    def delete(self, request, *args, **kwargs):
        return Response({"delete": "working"})


class EMRModelViewSet(
    EMRCreateMixin,
    EMRRetrieveMixin,
    EMRListMixin,
    EMRQuestionnaireMixin,
    EMRBaseViewSet,
):
    pass


# DONE Maybe use a different pydantic model for request and response, Response does not need validations or defined Types
# DONE Maybe switch to use custom mixins
# Complete update and delete logic
# DONE Create valuesets for allergy intolerance and write the logic for validation
# DONE Convert to questionnaire spec and store it somewhere and return on the questionnaire API
# Write the history function based on the update.

# DONE Validate valueset data on create
# DONEAdd option for extra validation being written in the model

# DONE Model the questionnaire object in pydantic
# DONE Create CRUD for questionnaire
# DONE Create definition returning API for questionnaire
# Submit API for Questionnaire -> Implicitly requires observations to be completed

# Create API's for valuesets and code concepts ( integrations already built  )
