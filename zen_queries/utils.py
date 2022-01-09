from django.db.models.query import QuerySet
from typing import TypeVar

T = TypeVar("T")


def fetch(queryset: T) -> T:
    queryset._fetch_all()  # type: ignore
    return queryset
