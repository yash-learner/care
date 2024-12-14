from datetime import timezone, timedelta

from pydantic import BaseModel, field_validator, Field
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from care.emr.api.viewsets.base import EMRBaseViewSet
from care.facility.api.serializers.patient_otp import rand_pass
from care.facility.models import PatientMobileOTP
from care.utils.models.validators import mobile_validator
from django.conf import settings
from django.utils import timezone

from care.utils.sms.send_sms import send_sms
from config.patient_otp_token import PatientToken


class OTPLoginRequestSpec(BaseModel):
    phone_number: str

    @field_validator("phone_number")
    @classmethod
    def validate_phone_number(cls, value):
        try:
            mobile_validator(value)
        except Exception as e:
            raise ValueError("Invalid phone number")
        return value

class OTPLoginSpec(OTPLoginRequestSpec):
    otp: str = Field(min_length=settings.OTP_LENGTH , max_length=settings.OTP_LENGTH )


class OTPLoginView(EMRBaseViewSet):

    authentication_classes = []
    permission_classes = []

    @action(detail=False, methods=["POST"])
    def send(self, request):
        data = OTPLoginRequestSpec(**request.data)
        sent_otps = PatientMobileOTP.objects.filter(
            created_date__gte=(
                timezone.now() - timedelta(settings.OTP_REPEAT_WINDOW)
            ),
            is_used=False,
            phone_number=data.phone_number,
        )
        if sent_otps.count() >= settings.OTP_MAX_REPEATS_WINDOW:
            raise ValidationError({"phone_number": "Max Retries has exceeded"})
        otp_obj = PatientMobileOTP(phone_number=data.phone_number , otp=rand_pass(settings.OTP_LENGTH))
        if settings.USE_SMS:
            send_sms(
                otp_obj.phone_number,
                (
                    f"Open Healthcare Network Patient Management System Login, OTP is {otp_obj.otp} . "
                    "Please do not share this Confidential Login Token with anyone else"
                ),
            )
        elif settings.DEBUG:
            import logging
            logging.info(f"{otp_obj.otp} {otp_obj.phone_number}")
        otp_obj.save()
        return Response({"otp" : "generated"})


    @action(detail=False, methods=["POST"])
    def login(self, request):
        data = OTPLoginSpec(**request.data)
        otp_object = PatientMobileOTP.objects.filter(
            phone_number=data.phone_number, otp=data.otp, is_used=False
        ).first()
        if not otp_object:
            raise ValidationError({"otp": "Invalid OTP"})

        # otp_object.is_used = True # TODO UNCOMMENT THIS !!
        otp_object.save()

        token = PatientToken()
        token["phone_number"] = data.phone_number

        return Response({"access": str(token)})
