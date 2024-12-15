from pydantic import UUID4
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from care.emr.api.viewsets.base import EMRModelViewSet, EMRModelReadOnlyViewSet, EMRRetrieveMixin, EMRBaseViewSet
from care.emr.api.viewsets.scheduling import SlotsForDayRequestSpec, SlotViewSet, AppointmentBookingSpec
from care.emr.models import TokenSlot, TokenBooking
from care.emr.resources.scheduling.slot.spec import TokenSlotBaseSpec, TokenBookingReadSpec, TokenBookingRetrieveSpec
from care.facility.models import PatientRegistration
from config.patient_otp_authentication import OTPAuthenticatedPermission, JWTTokenPatientAuthentication


class SlotsForDayRequestSpec(SlotsForDayRequestSpec):
    facility: UUID4


class OTPSlotViewSet(EMRRetrieveMixin, EMRBaseViewSet):
    authentication_classes = [JWTTokenPatientAuthentication]
    permission_classes = [OTPAuthenticatedPermission]
    database_model = TokenSlot
    pydantic_read_model = TokenBookingRetrieveSpec

    @action(detail=False, methods=["POST"])
    def get_slots_for_day(self, request, *args, **kwargs):
        request_data = SlotsForDayRequestSpec(**request.data)
        return SlotViewSet.get_slots_for_day_handler(request_data.facility, request.data)


    @action(detail=True, methods=["POST"])
    def create_appointment(self, request, *args, **kwargs):
        request_data = AppointmentBookingSpec(**request.data)
        if not PatientRegistration.objects.filter(external_id=request_data.patient , phone_number=request.user.phone_number).exists():
            raise ValidationError("Patient not allowed ")
        return SlotViewSet.create_appointment_handler(self.get_object() , request.data , None)


    @action(detail=False,methods=["GET"])
    def get_appointments(self,request,*args,**kwargs):
        appointments = TokenBooking.objects.filter(patient__phone_number=request.user.phone_number)
        return Response({"results" : [TokenBookingReadSpec.serialize(obj).model_dump(exclude=["meta"]) for obj in appointments]})
