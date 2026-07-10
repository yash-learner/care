import re
import secrets
import string
from collections import UserDict


class FixtureError(Exception):
    pass


class AttributeDict(UserDict):
    """Allows attribute access (obj.id for a dict api response)."""

    def __getattr__(self, key):
        try:
            return self.data[key]
        except KeyError:
            raise AttributeError(key) from None

    def __setattr__(self, key, value):
        if (
            key == "data"
        ):  # this is to avoid overwriting the inner data dict of UserDict
            super().__setattr__(key, value)
        else:
            self.data[key] = value


def to_attr_dict(obj):
    if isinstance(obj, dict):
        return AttributeDict({k: to_attr_dict(v) for k, v in obj.items()})
    if isinstance(obj, list):
        return [to_attr_dict(item) for item in obj]
    return obj


def generate_phone_number():
    prefix = secrets.choice(["6", "7", "8", "9"])
    suffix = "".join(secrets.choice(string.digits) for _ in range(9))
    return f"+91{prefix}{suffix}"


def slugify(text, max_length=36):
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:max_length]
    return slug if len(slug) >= 5 else slug.ljust(5, "-")  # noqa: PLR2004
