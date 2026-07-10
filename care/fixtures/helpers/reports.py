import json
from pathlib import Path

from django.urls import reverse

from care.fixtures.helpers.utils import FixtureError


class ReportFixturesMixin:
    """Report templates."""

    def create_template(
        self,
        name,
        slug_value,
        template_data,
        template_type="discharge_summary",
        context="encounter_base",
        facility=None,
        **kwargs,
    ):
        url = reverse("template-list")
        data = {
            "name": name,
            "slug_value": slug_value,
            "template_data": template_data,
            "template_type": template_type,
            "context": context,
            "status": "active",
            "default_format": "html",
            "facility": facility,
            **kwargs,
        }
        return self.post(url, data)

    def load_templates_from_file(
        self, facility=None, path="data/template_fixtures.json"
    ):
        fixture_path = Path(path)
        if not fixture_path.exists():
            return []
        with fixture_path.open() as f:
            templates = json.load(f)
        results = []
        for entry in templates:
            try:
                results.append(self.create_template(facility=facility, **entry))
            except FixtureError:
                pass
        return results
