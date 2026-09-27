# Architecture

```
Python simulator ──▶ Kinesis (1 shard) ──▶ Databricks Structured Streaming
                                               │
                                     bronze (raw events)
                                               │  dedup, watermark 2 min, schema checks
                                     silver (clean events)
                                               │  stateful trip tracking, H3 windows
                                     gold: active_trips, surge_by_h3, late_trip_alerts
                                               │
                              Streamlit map  ◀─┴─▶  SNS email/Slack alert
```

All Delta tables live in S3 under `s3://<bucket>/{bronze,silver,gold}/`.
Streaming checkpoints live under `s3://<bucket>/checkpoints/`.

## Local development
Use `docker/docker-compose.yml` (Redpanda) instead of Kinesis; the simulator's
Kafka sink and Databricks' Kafka source are drop-in replacements.
