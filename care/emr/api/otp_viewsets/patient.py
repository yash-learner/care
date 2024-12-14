from care.emr.api.viewsets.base import EMRBaseViewSet


class PatientOTPView(EMRBaseViewSet):

    authentication_classes = []
    permission_classes = []

    # Allow Creates at reduced spec based on the flow
    # Allow Login at reduced spec based on the flow

    def create(self):
        pass
