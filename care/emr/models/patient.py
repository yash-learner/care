from django.contrib.postgres.fields import ArrayField
from django.core.validators import MinValueValidator
from django.db import models

from care.emr.models import EMRBaseModel
from care.users.models import User
from care.utils.models.validators import mobile_or_landline_number_validator


class Patient(EMRBaseModel):
    name = models.CharField(max_length=200, default="")
    gender = models.CharField(max_length=10, default="")

    phone_number = models.CharField(
        max_length=14, validators=[mobile_or_landline_number_validator], default=""
    )

    emergency_phone_number = models.CharField(
        max_length=14, validators=[mobile_or_landline_number_validator], default=""
    )
    address = models.TextField(default="")
    permanent_address = models.TextField(default="")

    pincode = models.IntegerField(default=0, blank=True, null=True)

    date_of_birth = models.DateField(default=None, null=True)
    year_of_birth = models.IntegerField(validators=[MinValueValidator(1900)], null=True)
    deceased_datetime = models.DateTimeField(default=None, null=True, blank=True)

    marital_status = models.CharField(max_length=50, default="")

    blood_group = models.CharField()

    geo_organization = models.ForeignKey(
        "emr.Organization", on_delete=models.SET_NULL, null=True, blank=True
    )

    organization_cache = ArrayField(models.IntegerField(), default=list)

    users_cache = ArrayField(models.IntegerField(), default=list)

    def rebuild_organization_cache(self):
        organization_parents = []
        if self.geo_organization:
            organization_parents.extend(self.geo_organization.parent_cache)
            organization_parents.append(self.geo_organization.id)
        if self.id:
            for patient_organization in PatientOrganization.objects.filter(
                patient_id=self.id
            ):
                organization_parents.extend(
                    patient_organization.organization.parent_cache
                )
                organization_parents.append(patient_organization.id)

        self.organization_cache = list(set(organization_parents))

    def rebuild_users_cache(self):
        users = list(
            PatientUser.objects.filter(patient=self).values_list("user_id", flat=True)
        )
        self.users_cache = users

    def save(self, *args, **kwargs) -> None:
        self.rebuild_organization_cache()
        if self.date_of_birth and not self.year_of_birth:
            self.year_of_birth = self.date_of_birth.year
        super().save(*args, **kwargs)


class PatientOrganization(EMRBaseModel):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    organization = models.ForeignKey("emr.Organization", on_delete=models.CASCADE)
    # TODO : Add Role here to deny certain permissions for certain organizations

    def save(self, *args, **kwargs) -> None:
        super().save(*args, **kwargs)
        self.patient.rebuild_organization_cache()
        self.patient.save(update_fields=["organization_cache"])


class PatientUser(EMRBaseModel):
    """
    Add a user that can access the patient
    """

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    role = models.ForeignKey("security.RoleModel", on_delete=models.PROTECT)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.patient.save()
