# Architecture

```
Python simulator ──▶ SQS queue ──▶ Lambda batcher (every 10 s / 500 msgs)
                                          │  gzipped JSON lines
                                s3://<bucket>/raw-events/year=/month=/day=/hour=/
                                          │
                            Databricks Auto Loader (Structured Streaming)
                                          │
                                bronze (raw events, Delta)
                                          │  dedup, watermark 2 min, schema checks
                                silver (clean events)
                                          │  stateful trip tracking, H3 windows
                        gold: active_trips, surge_by_h3, late_trip_alerts
                                          │
                       Streamlit map  ◀───┴───▶  SNS email alert
```

## Why SQS + Lambda instead of Kinesis
The project runs on the post-July-2025 AWS Free plan, which blocks Kinesis Data
Streams and Firehose. SQS + Lambda + S3 are always-free within generous limits
and give the same landing pattern (hourly-partitioned JSON in S3) that Auto
Loader expects. Swapping in Kinesis later means changing only `infra/` and the
simulator sink; the Databricks layer is unaffected.

## Latency budget
- Simulator tick: 2 s
- Lambda batching window: ≤ 10 s
- Auto Loader trigger: 10 s
- End-to-end raw → bronze: ~20–30 s

## Local development
`docker/docker-compose.yml` runs Redpanda (Kafka) so the producer and a local
consumer can be developed without AWS. The simulator's `file` sink also works
for offline testing.
