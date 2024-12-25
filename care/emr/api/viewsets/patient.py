from care.emr.api.viewsets.base import EMRModelReadOnlyViewSet
from care.emr.resources.patient.spec import PatientListSpec, PatientRetrieveSpec
from care.facility.models import PatientRegistration


class NewPatientViewSet(EMRModelReadOnlyViewSet):
    database_model = PatientRegistration
    pydantic_read_model = PatientListSpec
    pydantic_retrieve_model = PatientRetrieveSpec

    def get_queryset(self):
        return super().get_queryset().select_related("created_by", "geo_organization")
