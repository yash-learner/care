from care.emr.api.viewsets.base import EMRBaseViewSet


class EncounterViewSet(EMRBaseViewSet):
    lookup_field = "external_id"
