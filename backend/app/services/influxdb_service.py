"""
InfluxDB service for resolving simulation_id from the simulations bucket.

Used when simulation_id is not available from the filesystem (e.g. output_directory
not accessible). Queries InfluxDB for distinct simulation_id values in the test run's
time window so the UI can show the ID used in Grafana/InfluxDB.
"""

from datetime import datetime, timezone
from typing import List, Optional

import structlog

from app.core.config import settings

logger = structlog.get_logger()

try:
    from influxdb_client import InfluxDBClient
    from influxdb_client.client.query_api import QueryApi
    INFLUXDB_AVAILABLE = True
except ImportError:
    INFLUXDB_AVAILABLE = False
    InfluxDBClient = None  # type: ignore
    QueryApi = None  # type: ignore


def get_simulation_ids_in_time_range(
    start: datetime,
    end: Optional[datetime] = None,
    bucket: Optional[str] = None,
    measurement: str = "simulation_data",
) -> List[str]:
    """
    Query InfluxDB for distinct simulation_id values that have data in the given time range.

    Returns a list of simulation_id strings (e.g. ["20260227_082647"]). Empty if
    InfluxDB is not configured, query fails, or no data in range.
    """
    if not INFLUXDB_AVAILABLE:
        logger.debug("InfluxDB client not available, skipping simulation_id lookup")
        return []
    if not settings.INFLUXDB_TOKEN or not settings.INFLUXDB_URL:
        logger.debug("InfluxDB not configured (missing token or url), skipping simulation_id lookup")
        return []

    bucket = bucket or settings.INFLUXDB_BUCKET
    if not end or end <= start:
        from datetime import timedelta
        end = start + timedelta(hours=1)

    # Ensure timezone-aware for Flux
    if start.tzinfo is None:
        start = start.replace(tzinfo=timezone.utc)
    if end.tzinfo is None:
        end = end.replace(tzinfo=timezone.utc)
    start_rfc = start.strftime("%Y-%m-%dT%H:%M:%SZ")
    end_rfc = end.strftime("%Y-%m-%dT%H:%M:%SZ")

    flux = (
        f'from(bucket: "{bucket}")'
        f' |> range(start: time(v: "{start_rfc}"), stop: time(v: "{end_rfc}"))'
        f' |> filter(fn: (r) => r["_measurement"] == "{measurement}")'
        ' |> distinct(column: "simulation_id")'
    )

    ids: List[str] = []
    try:
        client = InfluxDBClient(
            url=settings.INFLUXDB_URL,
            token=settings.INFLUXDB_TOKEN,
            org=settings.INFLUXDB_ORG,
        )
        query_api = client.query_api()
        result = query_api.query(org=settings.INFLUXDB_ORG, query=flux)
        client.close()

        for table in result:
            for record in table.records:
                sid = record.get_value()
                if isinstance(sid, str) and sid.strip():
                    ids.append(sid.strip())
        ids = list(dict.fromkeys(ids))  # preserve order, dedupe
        logger.debug("InfluxDB simulation_id lookup", count=len(ids), simulation_ids=ids[:5])
    except Exception as e:
        logger.warning("InfluxDB simulation_id query failed", error=str(e))
    return ids
