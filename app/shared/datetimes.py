from datetime import datetime, timezone
from typing import Annotated

from pydantic import PlainSerializer


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def iso_ms(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%S") + f".{dt.microsecond // 1000:03d}Z"


def now_iso() -> str:
    return (
        datetime.now(timezone.utc)
        .isoformat(timespec="milliseconds")
        .replace("+00:00", "Z")
    )


ApiDatetime = Annotated[datetime, PlainSerializer(iso_ms, return_type=str)]
