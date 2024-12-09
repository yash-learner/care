from datetime import UTC, datetime

from django.db.models import Q
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response

from care.emr.api.viewsets.base import EMRModelViewSet
from care.emr.fhir.schema.base import DateTime
from care.emr.models.specimen import Specimen
from care.emr.resources.specimen.spec import (
    SpecimenCollectRequest,
    SpecimenProcessRequest,
    SpecimenReadSpec,
    SpecimenReceiveAtLabRequest,
    SpecimenSendToLabRequest,
    SpecimenSpec,
    StatusChoices,
)


@extend_schema_view(
    create=extend_schema(request=SpecimenSpec),
)
class SpecimenViewSet(EMRModelViewSet):
    database_model = Specimen
    pydantic_model = SpecimenSpec
    pydantic_read_model = SpecimenReadSpec

    def get_object(self) -> Specimen:
        return get_object_or_404(
            self.get_queryset(),
            Q(external_id__iexact=self.kwargs[self.lookup_field])
            | Q(identifier=self.kwargs[self.lookup_field])
            | Q(accession_identifier=self.kwargs[self.lookup_field]),
        )

    @extend_schema(
        request=SpecimenCollectRequest,
        responses={200: SpecimenReadSpec},
        tags=["specimen"],
    )
    @action(detail=True, methods=["POST"])
    def collect(self, request, *args, **kwargs):
        data = SpecimenCollectRequest(**request.data)
        specimen = self.get_object()

        specimen.identifier = data.identifier
        specimen.status = StatusChoices.available
        specimen.collected_at = datetime.now(UTC)
        specimen.collected_by = request.user
        specimen.save()

        return Response(
            self.get_read_pydantic_model()
            .serialize(specimen)
            .model_dump(exclude=["meta"]),
        )

    @extend_schema(
        request=SpecimenSendToLabRequest,
        responses={200: SpecimenReadSpec},
        tags=["specimen"],
    )
    @action(detail=True, methods=["POST"])
    def send_to_lab(self, request, *args, **kwargs):
        data = SpecimenSendToLabRequest(**request.data)
        specimen = self.get_object()
        service_request = specimen.request

        service_request.location = data.lab
        specimen.dispatched_at = datetime.now(UTC)
        specimen.dispatched_by = request.user
        service_request.save()
        specimen.save()

        return Response(
            self.get_read_pydantic_model()
            .serialize(specimen)
            .model_dump(exclude=["meta"]),
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        request=SpecimenReceiveAtLabRequest,
        responses={200: SpecimenReadSpec},
        tags=["specimen"],
    )
    @action(detail=True, methods=["POST"])
    def receive_at_lab(self, request, *args, **kwargs):
        data = SpecimenReceiveAtLabRequest(**request.data)
        specimen = self.get_object()
        note = data.note

        specimen.accession_identifier = data.accession_identifier
        specimen.condition = data.condition
        specimen.received_at = datetime.now(UTC)
        specimen.received_by = request.user
        if note:
            note.authorReference = {"id": request.user.external_id}
            note.time = DateTime(datetime.now(UTC).isoformat())
            specimen.note.append(note.model_dump(mode="json"))
        specimen.save()

        return Response(
            self.get_read_pydantic_model()
            .serialize(specimen)
            .model_dump(exclude=["meta"]),
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        request=SpecimenProcessRequest,
        responses={200: SpecimenReadSpec},
        tags=["specimen"],
    )
    @action(detail=True, methods=["POST"])
    def process(self, request, *args, **kwargs):
        data = SpecimenProcessRequest(**request.data)
        specimen = self.get_object()

        processes = []
        for process in data.process:
            if not process.time:
                process.time = datetime.now(UTC)

            if not process.performer:
                process.performer = request.user.external_id

            processes.append(process.model_dump(mode="json"))

        specimen.processing.extend(processes)
        specimen.save()

        return Response(
            self.get_read_pydantic_model()
            .serialize(specimen)
            .model_dump(exclude=["meta"]),
            status=status.HTTP_200_OK,
        )
