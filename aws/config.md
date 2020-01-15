# EC2

- Region: us-east-1 (for historical reasons)
- Storage: 16GB
- OS: ubuntu 16.04
- Size: t2.medium
- Be sure to set "Auto-assign Public IP" to True

# Networking

- Make sure that the `monitoring` lambda is on the VPC and is associated with
  VPC's subnets
- Create a NAT Gateway for the VPC. Make a route table that maps `0.0.0.0/0` to
  the created NAT, and associate that with the VPC's subnets
- Create VPC endpoints for S3 and SNS
- There needs to be 1 route tables:
  - It should maps `0.0.0.0/0` to the VPC's inet gateway (for internal
    connections)
  - It should include a route to the S3 VPC endpoint
  - It should include a route to the SNS VPC endpoint
- More info about Lambda/VPC:
  https://aws.amazon.com/premiumsupport/knowledge-center/internet-access-lambda-function/

# Pre-Event Checklist

- [ ] Take a snapshot of the previous event if not already done
- [ ] Update the Hugo config to have the countdown for "next" event. Deploy
      countdown and snapshot-ed previous event.
- [ ] Setup new EC2 instance following the above steps
- [ ] Follow the instructions in `bootstrap_aws.sh` to setup the EC2 instance w/
      Docker
- [ ] Deploy the zappa lambda_suite:
  - `zappa deploy prod`
  - `zappa deploy cache_databases`
  - `zappa deploy monitoring_databases`
  - `zappa deploy monitoring_api`
- [ ] Setup cloud watch dashboard to track new EC2 instance
- [ ] Make sure you can connect to postgres over SSH
- [ ] Make sure that `monitoring` lambda isn't timing out
- [ ] Trigger a test alarm with `zappa invoke monitoring monitoring.test_alarm`
      and make sure it sends a text/email
- [ ] Manually invoke health checks and make sure they return "no error".
  - [ ] `zappa invoke monitoring_api monitoring.health_check_api`
  - [ ] `zappa invoke monitoring_databases monitoring.health_check_databases`

# Post-Event Checklist

- [ ] Export DB tables via Postico and save to site/data folder
- [ ] Download latest db cache files from S3 and safe to site/data folder
- [ ] Do a DB dump w/ `pg_dump`
  - Might need to install postgresql 9.6 on the host machine
    (https://askubuntu.com/a/831293)
  - Run with
    `/usr/lib/postgresql/9.6/bin/pg_dump -h localhost -U gdqstatus > db_dump.sql`
- [ ] Set frontend to offline mode
- [ ] Delete the NAT gateway and VPC endpoints
- [ ] Delete object versions from S3 cache
  - https://stackoverflow.com/a/41399166

```python
#!/usr/bin/env python
import boto3

s3 = boto3.resource('s3')
bucket = s3.Bucket('your-bucket-name')
bucket.object_versions.all().delete()
```
