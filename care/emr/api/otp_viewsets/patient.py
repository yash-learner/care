from care.emr.api.viewsets.base import EMRBaseViewSet, EMRListMixin
from care.emr.resources.patient.otp_based_flow import PatientOTPReadSpec
from care.facility.models import PatientRegistration
from config.patient_otp_authentication import (
    JWTTokenPatientAuthentication,
    OTPAuthenticatedPermission,
)


class PatientOTPView(EMRListMixin, EMRBaseViewSet):
    authentication_classes = [JWTTokenPatientAuthentication]
    permission_classes = [OTPAuthenticatedPermission]
    pydantic_read_model = PatientOTPReadSpec
    # Allow Creates at reduced spec based on the flow

    def get_queryset(self):
        return PatientRegistration.objects.filter(
            phone_number=self.request.user.phone_number
        )

    def create(self, request):
        pass
