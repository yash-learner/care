from pydantic import BaseModel
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response

from care.emr.api.viewsets.base import EMRModelViewSet
from care.emr.models import FileUpload
from care.emr.resources.file_upload.spec import (
    FileUploadCreateSpec,
    FileUploadRetrieveSpec,
    FileUploadUpdateSpec, FileUploadListSpec,
)

from django.utils import timezone

def file_authorizer(file_type, associating_id, permission):
    return


class FileUploadViewSet(EMRModelViewSet):
    database_model = FileUpload
    pydantic_model = FileUploadCreateSpec
    pydantic_retrieve_model = FileUploadRetrieveSpec
    pydantic_update_model = FileUploadUpdateSpec
    pydantic_read_model = FileUploadListSpec

    def authorize_create(self, instance):
        pass

    def get_queryset(self):
        if self.action == "list":
            if (
                "file_type" not in self.request.GET
                and "associating_id" not in self.request.GET
            ):
                raise PermissionError("Cannot filter files")
            file_authorizer(
                self.request.GET.get("file_type"),
                self.request.GET.get("associating_id"),
                "read",
            )
            return (
                super()
                .get_queryset()
                .filter(
                    file_type=self.request.GET.get("file_type"),
                    associating_id=self.request.GET.get("associating_id"),
                )
            )
        obj = get_object_or_404(FileUpload, external_id=self.kwargs["external_id"])
        file_authorizer(obj.file_type, obj.associating_id, "read")
        return super().get_queryset()


    @action(detail=True, methods=["POST"])
    def mark_upload_completed(self, request,*args, **kwargs):
        obj = self.get_object()
        file_authorizer(obj.file_type, obj.associating_id, "write")
        obj.upload_completed = True
        obj.save(update_fields=["upload_completed"])
        return Response(FileUploadListSpec.serialize(obj).to_json())

    class ArchiveRequestSpec(BaseModel):
        archive_reason : str

    @action(detail=True, methods=["POST"])
    def archive(self, request,*args, **kwargs):
        obj = self.get_object()
        request_data = self.ArchiveRequestSpec(**request.data)
        file_authorizer(obj.file_type, obj.associating_id, "write")
        obj.is_archived = True
        obj.archive_reason = request_data.archive_reason
        obj.archived_datetime = timezone.now()
        obj.archived_by = request.user
        obj.save(update_fields=["is_archived" , "archive_reason" , "archived_datetime" , "archived_by"])
        return Response(FileUploadListSpec.serialize(obj).to_json())
