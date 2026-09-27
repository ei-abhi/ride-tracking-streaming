"""
SQS -> S3 batcher.

Triggered by an SQS event source mapping with a batch of up to 500 messages.
Writes all message bodies as one gzipped JSON-lines object to S3, partitioned
by the current UTC hour, so Databricks Auto Loader can pick it up.
"""

import gzip
import json
import os
import uuid
from datetime import datetime, timezone

import boto3

s3 = boto3.client("s3")
BUCKET = os.environ["BUCKET"]
PREFIX = os.environ.get("PREFIX", "raw-events")


def handler(event, context):
    records = event.get("Records", [])
    if not records:
        return {"batchItemFailures": []}

    lines = []
    failures = []
    for r in records:
        body = r.get("body", "")
        try:
            json.loads(body)          # validate it is JSON; keep raw text as-is
            lines.append(body)
        except json.JSONDecodeError:
            failures.append({"itemIdentifier": r["messageId"]})  # -> retries, then DLQ

    if lines:
        now = datetime.now(timezone.utc)
        key = (
            f"{PREFIX}/year={now:%Y}/month={now:%m}/day={now:%d}/hour={now:%H}/"
            f"batch-{now:%Y%m%dT%H%M%S}-{uuid.uuid4().hex[:8]}.json.gz"
        )
        payload = gzip.compress(("\n".join(lines) + "\n").encode("utf-8"))
        s3.put_object(Bucket=BUCKET, Key=key, Body=payload, ContentType="application/json",
                      ContentEncoding="gzip")
        print(f"wrote {len(lines)} events to s3://{BUCKET}/{key}")

    return {"batchItemFailures": failures}
