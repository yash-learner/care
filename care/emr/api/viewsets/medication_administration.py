from django.db import models
from django.db.models import F
from django.db.models.functions import Cast
from django_filters import rest_framework as filters

from care.emr.api.viewsets.base import EMRModelViewSet
from care.emr.models.medication_administration import MedicationAdministration
from care.emr.resources.medication.administration.spec import (
    MedicationAdministrationReadSpec,
    MedicationAdministrationSpec,
)


class MedicationAdministrationFilter(filters.FilterSet):
    encounter = filters.UUIDFilter(field_name="encounter__external_id")
    request = filters.UUIDFilter(field_name="request__external_id")
    occurrence_period_start = filters.DateTimeFromToRangeFilter(
        method="filter_occurrence_period_start"
    )
    occurrence_period_end = filters.DateTimeFromToRangeFilter(
        method="filter_occurrence_period_end"
    )

    def filter_occurrence_period_start(self, queryset, name, value):
        """
        Filters by occurrence_period.start using DateTimeFromToRangeFilter.
        """

        if value:
            queryset = (
                queryset.annotate(
                    occurrence_start_datetime=Cast(
                        F("occurrence_period__start"),
                        output_field=models.TextField(),
                    )
                )
                .annotate(
                    occurrence_start_datetime_parsed=Cast(
                        F("occurrence_start_datetime"),
                        output_field=models.DateTimeField(),
                    )
                )
                .filter(
                    occurrence_start_datetime_parsed__range=(value.start, value.stop)
                )
            )
        return queryset

    def filter_occurrence_period_end(self, queryset, name, value):
        """
        Filters by occurrence_period.end using DateTimeFromToRangeFilter.
        """

        if value:
            queryset = (
                queryset.annotate(
                    occurrence_end_datetime=Cast(
                        F("occurrence_period__end"), output_field=models.TextField()
                    )
                )
                .annotate(
                    occurrence_end_datetime_parsed=Cast(
                        F("occurrence_end_datetime"),
                        output_field=models.DateTimeField(),
                    )
                )
                .filter(occurrence_end_datetime_parsed__range=(value.start, value.stop))
            )
        return queryset


class MedicationAdministrationViewSet(EMRModelViewSet):
    database_model = MedicationAdministration
    pydantic_model = MedicationAdministrationSpec
    pydantic_read_model = MedicationAdministrationReadSpec
    filterset_class = MedicationAdministrationFilter
    filter_backends = [filters.DjangoFilterBackend]
    CREATE_QUESTIONNAIRE_RESPONSE = False

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .filter(patient__external_id=self.kwargs["patient_external_id"])
            .select_related("patient", "encounter", "created_by", "updated_by")
        )
