import json
import os
import boto3

targetGroupARN = os.getenv('TARGETGROUP_ARN')
targetGroupPort = os.getenv('TARGETGROUP_PORT')


def handler(event, context):
    # Log the event argument for debugging and for use in local development.
    print(json.dumps(event))

    for event in event['Records']:
        if event['eventName'] != 'INSERT' and event['eventName'] != 'MODIFY':
            continue
        addresses = json.loads(event['dynamodb']['NewImage']['Address']['S'])

        # Target group client
        targetGroup = boto3.client('elbv2')
        # Get targets from target group
        targets = targetGroup.describe_target_health(
            TargetGroupArn=targetGroupARN)
        if 'TargetHealthDescriptions' in targets:
            for target in targets['TargetHealthDescriptions']:
                if target['Target']['Id'] in addresses and target['Target']['Port'] == int(targetGroupPort):
                    # Remove item from adresses
                    print(target['Target']['Id'], 'remove from addresses list')
                    addresses.remove(target['Target']['Id'])
                    continue
                if target['Target']['Id'] not in addresses and target['Target']['Port'] == int(targetGroupPort):
                    # Remove target from target group
                    print(target['Target']['Id'], 'remove from target group')
                    targetGroup.deregister_targets(TargetGroupArn=targetGroupARN,  Targets=[
                                                   {'Id': target['Target']['Id'], 'Port': int(targetGroupPort)}])
            # add address to target group
            for address in addresses:
                print(address, 'add to target group')
                targetGroup.register_targets(TargetGroupArn=targetGroupARN,  Targets=[
                    {'Id': address, 'Port': int(targetGroupPort)}])
    return {}
