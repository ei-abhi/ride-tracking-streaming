# Ride tracking — real-time streaming data platform

Real-time driver location pipeline: Python simulator → SQS → Lambda batcher → S3 → Databricks Auto Loader + Structured Streaming → Delta Lake (bronze/silver/gold) → live map dashboard + SNS alerts.

Runs entirely within the AWS Free plan (SQS, Lambda, S3, SNS are always-free within limits) and Databricks Free Edition.

## Architecture
See `docs/architecture.md`.

## Repo layout
```
producer/      Python driver simulator (SQS / file / stdout sinks)
infra/         Terraform for SQS, Lambda, S3, IAM, SNS (+ lambda/ source)
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
terraform apply       # creates SQS queue, Lambda batcher, S3 bucket, IAM roles, SNS topic
```

## Teardown (do this after every demo session)
```bash
cd infra/terraform && terraform destroy
```
