"""Small datetime helpers for normalizing mixed offset-naive/aware values."""
from datetime import datetime, timezone


def as_naive(dt: datetime) -> datetime:
    """Return an offset-naive datetime that can be safely compared.

    Mixed offset-naive and offset-aware datetimes cannot be compared or
    aggregated with ``min``/``max``. We normalize aware datetimes to UTC and
    then drop tzinfo so all values are comparable.
    """
    if dt is None:
        return None
    if dt.tzinfo is not None and dt.utcoffset() is not None:
        return dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt
