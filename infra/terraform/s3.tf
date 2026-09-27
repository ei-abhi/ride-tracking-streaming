resource "aws_s3_bucket" "lake" {
  bucket        = var.bucket_name
  force_destroy = true # lets terraform destroy delete objects too (demo project)
}

resource "aws_s3_bucket_versioning" "lake" {
  bucket = aws_s3_bucket.lake.id
  versioning_configuration {
    status = "Disabled"
  }
}

resource "aws_s3_bucket_public_access_block" "lake" {
  bucket                  = aws_s3_bucket.lake.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Medallion layout prefixes (S3 has no real folders; these are markers)
resource "aws_s3_object" "layers" {
  for_each = toset(["bronze/", "silver/", "gold/", "checkpoints/", "raw-events/"])
  bucket   = aws_s3_bucket.lake.id
  key      = each.value
}

# Auto-expire raw archive after 7 days to stay inside the 5 GB free tier
resource "aws_s3_bucket_lifecycle_configuration" "lake" {
  bucket = aws_s3_bucket.lake.id
  rule {
    id     = "expire-raw-events"
    status = "Enabled"
    filter {
      prefix = "raw-events/"
    }
    expiration {
      days = 7
    }
  }
}
