from care.emr.api.viewsets.base import (
    EMRBaseViewSet,
    EMRCreateMixin,
    EMRDeleteMixin,
    EMRListMixin,
    EMRModelViewSet,
    EMRRetrieveMixin,
)
from care.emr.models.resource_request import ResourceRequest, ResourceRequestComment
from care.emr.resources.resource_request.spec import (
    ResourceRequestCommentCreateSpec,
    ResourceRequestCommentListSpec,
    ResourceRequestCommentRetrieveSpec,
    ResourceRequestCreateSpec,
    ResourceRequestListSpec,
    ResourceRequestRetrieveSpec,
)


class ResourceRequestViewSet(EMRModelViewSet):
    database_model = ResourceRequest
    pydantic_model = ResourceRequestCreateSpec
    pydantic_read_model = ResourceRequestListSpec
    pydantic_retrieve_model = ResourceRequestRetrieveSpec

    def get_queryset(self):
        return ResourceRequest.objects.all().select_related(
            "origin_facility",
            "approving_facility",
            "assigned_facility",
            "related_patient",
            "assigned_to",
        )


class ResourceRequestCommentViewSet(
    EMRCreateMixin, EMRRetrieveMixin, EMRListMixin, EMRDeleteMixin, EMRBaseViewSet
):
    database_model = ResourceRequestComment
    pydantic_model = ResourceRequestCommentCreateSpec
    pydantic_read_model = ResourceRequestCommentListSpec
    pydantic_retrieve_model = ResourceRequestCommentRetrieveSpec

    def perform_create(self, instance):
        instance.request = ResourceRequest.objects.get(
            external_id=self.kwargs["resource_external_id"]
        )
        super().perform_create(instance)

    def get_queryset(self):
        return ResourceRequestComment.objects.filter(
            request__external_id=self.kwargs["resource_external_id"]
        ).select_related("created_by")
