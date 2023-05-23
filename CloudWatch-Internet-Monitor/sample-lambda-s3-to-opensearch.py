'''
Amazon CloudWatch Internet Monitor supports sending logs to Amazon S3. 
When Amazon S3 receives a new log, it will trigger Lambda through an event. 
After decompressing the log, the Lambda will send the logs to Amazon OpenSearch Service in a suitable format.
--by Xulong Gao
'''
import boto3
import json
import requests
import gzip
from requests_aws4auth import AWS4Auth
region = 'Your Region' # e.g. us-west-1
service = 'es'
credentials = boto3.Session().get_credentials()
awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, region, service, session_token=credentials.token)
host = 'https://Your-OpenSearch-Endpoint'
# the OpenSearch Service Endpoint, e.g. https://search-mydomain.us-west-1.es.amazonaws.com
index = 'Your-Index-Name'
datatype = '_doc'
url = host + '/' + index + '/' + datatype
headers = { "Content-Type": "application/json" }
s3 = boto3.client('s3')
def lambda_handler(event, context):
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
            document = {
                "timestamp": message["timestamp"],
                "latitude": message["clientLocation"]["latitude"],
                "longitude": message["clientLocation"]["longitude"],
                "country": message["clientLocation"]["country"],
                "subdivision": message["clientLocation"]["subdivision"],
                "metro": message["clientLocation"]["metro"],
                "city": message["clientLocation"]["city"],
                "countryCode": message["clientLocation"]["countryCode"],
                "subdivisionCode": message["clientLocation"]["subdivisionCode"],
                "asn": message["clientLocation"]["asn"],
                "networkName": message["clientLocation"]["networkName"],
                "serviceLocation": message["serviceLocation"],
                "percentageOfTotalTraffic": message["percentageOfTotalTraffic"],
                "bytesIn": message["bytesIn"],
                "bytesOut": message["bytesOut"],
                "clientConnectionCount": message["clientConnectionCount"],
                "availabilityExperienceScore": message["internetHealth"]["availability"]["experienceScore"],
                "availabilityPercentageOfTotalTrafficImpacted": message["internetHealth"]["availability"]["percentageOfTotalTrafficImpacted"],
                "availabilityPercentageOfClientLocationImpacted": message["internetHealth"]["availability"]["percentageOfClientLocationImpacted"],
                "performanceExperienceScore": message["internetHealth"]["performance"]["experienceScore"],
                "performancePercentageOfTotalTrafficImpacted": message["internetHealth"]["performance"]["percentageOfTotalTrafficImpacted"],
                "performancePercentageOfClientLocationImpacted": message["internetHealth"]["performance"]["percentageOfClientLocationImpacted"],
                "p50RoundTripTime": message["internetHealth"]["performance"]["roundTripTime"]["p50"],
                "p90RoundTripTime": message["internetHealth"]["performance"]["roundTripTime"]["p90"],
                "p95RoundTripTime": message["internetHealth"]["performance"]["roundTripTime"]["p95"]
            }
            r = requests.post(url, auth=awsauth, json=document, headers=headers)