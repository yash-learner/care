from care.emr.api.viewsets.base import EMRBaseViewSet, EMRCreateMixin, EMRListMixin
from care.emr.resources.patient.otp_based_flow import (
    PatientOTPReadSpec,
    PatientOTPWriteSpec,
)
from care.facility.models import PatientRegistration
from config.patient_otp_authentication import (
    JWTTokenPatientAuthentication,
    OTPAuthenticatedPermission,
)


class PatientOTPView(EMRCreateMixin, EMRListMixin, EMRBaseViewSet):
    authentication_classes = [JWTTokenPatientAuthentication]
    permission_classes = [OTPAuthenticatedPermission]
    pydantic_model = PatientOTPWriteSpec
    pydantic_read_model = PatientOTPReadSpec

    def perform_create(self, instance):
        instance.phone_number = self.request.user.phone_number
        instance._history_user = None  # noqa SLF001
        instance.save()

    def get_queryset(self):
        return PatientRegistration.objects.filter(
            phone_number=self.request.user.phone_number
        )
