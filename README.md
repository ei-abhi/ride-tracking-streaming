# Ride tracking — real-time streaming data platform

Real-time driver location pipeline: Python simulator → Kinesis → Databricks Structured Streaming → Delta Lake (bronze/silver/gold) on S3 → live map dashboard + SNS alerts.

## Architecture
See `docs/architecture.md`.

## Repo layout
```
producer/      Python driver simulator (Kinesis / Kafka / stdout sinks)
infra/         Terraform for Kinesis, S3, IAM, SNS
databricks/    Streaming notebooks: bronze → silver → gold
dashboard/     Streamlit live map
docker/        Local Redpanda (Kafka) for zero-cost dev
tests/         pytest unit tests
.github/       CI workflow
```

## Quick start (local, zero cost)
```bash
make setup            # create venv and install deps
make local-stream     # start Redpanda in Docker
make simulate         # run the simulator to stdout
```

## Deploy to AWS (free tier)
```bash
cd infra/terraform
terraform init
terraform apply       # creates Kinesis stream, S3 bucket, IAM role, SNS topic
```

## Teardown (do this after every demo session)
```bash
cd infra/terraform && terraform destroy
```
