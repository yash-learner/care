from care.emr.api.viewsets.base import EMRModelViewSet
from care.facility.models import PatientConsultation


class EncounterViewSet(EMRModelViewSet):
    database_model = PatientConsultation
