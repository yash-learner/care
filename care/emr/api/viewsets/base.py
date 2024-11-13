from pydantic import ValidationError
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.viewsets import GenericViewSet,ModelViewSet
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler
from rest_framework.exceptions import ValidationError as DRFValidationError

from care.emr.models.base import EMRBaseModel
from care.emr.resources.base import FHIRResource

def fhir_exception_handler(exc, context):
    if isinstance(exc, ValidationError):
        return Response({"errors": exc.errors()}, status=400)

    return drf_exception_handler(exc, context)

class EMRBaseController:

    pydantic_model : FHIRResource = None
    database_model : EMRBaseModel = None
    pagination_class = LimitOffsetPagination

    def get_queryset(self):
        return self.database_model.objects.all()

    def get_object(self):
        queryset = self.get_queryset()
        obj = get_object_or_404(queryset , uuid=self.kwargs["pk"])
        return obj

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset().select_related("patient" , "encounter")
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request)
        if page is not None:
            data = [self.pydantic_model.from_database(obj).model_dump() for obj in page]
            return paginator.get_paginated_response(data)

        data = [self.pydantic_model.from_database(obj).model_dump() for obj in queryset]
        return Response(data)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        data = self.pydantic_model.from_orm_object(instance)
        return Response(data)

    def perform_create(self, instance):
        instance.save()

    def clean_create_data(self,request, *args, **kwargs):
        data = request.data
        data["encounter"] = kwargs["consultation_external_id"]
        return data

    def create(self, request, *args, **kwargs):
        clean_data = self.clean_create_data(request, *args, **kwargs)
        instance = self.pydantic_model(**clean_data)
        model_instance = instance.to_orm_object()
        self.perform_create(model_instance)
        return Response(self.pydantic_model.from_database(model_instance).model_dump())

    def update(self, request, *args, **kwargs):
        return Response({"update" : "working"})

    def delete(self, request, *args, **kwargs):
        return Response({"delete" : "working"})

class EMRBaseViewSet(GenericViewSet):

    emr_controller = None

    def get_exception_handler(self):
        return fhir_exception_handler

    def list(self, request, *args, **kwargs):
        return self.emr_controller().list(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        return self.emr_controller().retrieve(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        return self.emr_controller().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        return self.emr_controller().update(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        return self.emr_controller().delete(request, *args, **kwargs)

    @action(detail=True)
    def test(self, request, *args,**kwargs):
        return Response({"test" : "working"})


# Write a generic view that uses a pydantic spec to create a resource view, full CRUD, custom mixins
# Convert to questionnaire spec and store it somewhere and return on the questionnaire API
# Write the history function based on the update.

# Model the questionnaire object in pydantic
# Create CRUD for questionnaire
# Create defenition returning API for questionnaire
# Submit API for Questionnaire -> Implicitly requires observations to be completed

# Create API's for valuesets and code concepts ( integrations already built  )
