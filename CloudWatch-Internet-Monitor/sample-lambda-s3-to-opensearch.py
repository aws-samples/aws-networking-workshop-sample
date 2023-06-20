'''
Amazon CloudWatch Internet Monitor supports sending logs to Amazon S3. 
When Amazon S3 receives a new log, it will trigger Lambda through an event. 
After decompressing the log, the Lambda will send the logs to Amazon OpenSearch Service in a suitable format.
--by Xulong Gao
'''

'''
20230620 Update-XulongGao
1,auto create new index in every day
2,enhanced logical when round_trip_time is not exists
'''
import datetime
import pytz
import gzip
import json
import requests
import boto3
from requests_aws4auth import AWS4Auth

region = 'sa-east-1'  # e.g. us-west-1
service = 'es'
credentials = boto3.Session().get_credentials()
awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, region, service, session_token=credentials.token)
host = 'https://search-opensearch-demo-sms6ryhe5mz6zsh42qva6zdtey.sa-east-1.es.amazonaws.com'
datatype = '_doc'
headers = {"Content-Type": "application/json"}
s3 = boto3.client('s3')


def lambda_handler(event, context):
    tz = pytz.timezone('Asia/Shanghai')
    current_date = datetime.datetime.now(tz).strftime("%Y-%m-%d")
    index = 'lambda-s3-' + current_date
    url = host + '/' + index + '/' + datatype

    for record in event['Records']:
        bucket = record['s3']['bucket']['name']
        key = record['s3']['object']['key']
        obj = s3.get_object(Bucket=bucket, Key=key)
        body = obj['Body'].read()
        if key.endswith('.gz'):
            body = gzip.decompress(body)
        lines = body.splitlines()
        for line in lines:
            line = line.decode("utf-8")
            message = json.loads(line)  # parse JSON object
            
            #Check if round_trip_time exists
            round_trip_time = message["internetHealth"]["performance"].get("roundTripTime")
            p50_round_trip_time = round_trip_time.get("p50") if round_trip_time else None
            p90_round_trip_time = round_trip_time.get("p90") if round_trip_time else None
            p95_round_trip_time = round_trip_time.get("p95") if round_trip_time else None

            document = {
                "timestamp": message.get("timestamp"),
                "latitude": message["clientLocation"].get("latitude"),
                "longitude": message["clientLocation"].get("longitude"),
                "country": message["clientLocation"].get("country"),
                "subdivision": message["clientLocation"].get("subdivision"),
                "metro": message["clientLocation"].get("metro"),
                "city": message["clientLocation"].get("city"),
                "countryCode": message["clientLocation"].get("countryCode"),
                "subdivisionCode": message["clientLocation"].get("subdivisionCode"),
                "asn": message["clientLocation"].get("asn"),
                "networkName": message["clientLocation"].get("networkName"),
                "serviceLocation": message.get("serviceLocation"),
                "percentageOfTotalTraffic": message.get("percentageOfTotalTraffic"),
                "bytesIn": message.get("bytesIn"),
                "bytesOut": message.get("bytesOut"),
                "clientConnectionCount": message.get("clientConnectionCount"),
                "availabilityExperienceScore": message["internetHealth"]["availability"].get("experienceScore"),
                "availabilityPercentageOfTotalTrafficImpacted": message["internetHealth"]["availability"].get(
                    "percentageOfTotalTrafficImpacted"),
                "availabilityPercentageOfClientLocationImpacted": message["internetHealth"]["availability"].get(
                    "percentageOfClientLocationImpacted"),
                "performanceExperienceScore": message["internetHealth"]["performance"].get("experienceScore"),
                "performancePercentageOfTotalTrafficImpacted": message["internetHealth"]["performance"].get(
                    "percentageOfTotalTrafficImpacted"),
                "performancePercentageOfClientLocationImpacted": message["internetHealth"]["performance"].get(
                    "percentageOfClientLocationImpacted"),
                "p50RoundTripTime": p50_round_trip_time,
                "p90RoundTripTime": p90_round_trip_time,
                "p95RoundTripTime": p95_round_trip_time
            }

            r = requests.post(url, auth=awsauth, json=document, headers=headers)
