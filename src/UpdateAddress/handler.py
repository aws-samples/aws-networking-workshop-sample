import json
import os
import time
import socket
import boto3

domainName = os.getenv('DOMAIN_NAME')
tableName = os.getenv('TABLE_NAME')


def handler(event, context):
    # get all dns ip address from a domain name
    addresses = []
    infos = socket.getaddrinfo(
        domainName, None, family=socket.AF_INET, type=socket.SOCK_STREAM, proto=0, flags=0)
    for info in infos:
        addresses.append(info[4][0])
    # sort array
    addresses.sort()
    # remove duplicate
    addresses = list(set(addresses))
    # get timestamp
    now = int(time.time())

    # get domain, addresses and timestamp from dynamodb
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(tableName)
    response = table.get_item(Key={'Domain': domainName})

    if 'Item' in response and 'Timestamp' in response['Item'] and response['Item']['Timestamp'] > now:
        return {}

    if 'Item' not in response or response['Item']['Address'] != json.dumps(addresses):
        # write domain, addresses and timestamp to dynamodb
        item = {
            'Domain': domainName,
            'Address': json.dumps(addresses),
            'Timestamp': now
        }
        table.put_item(Item=item)

    return {}
