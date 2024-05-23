import json
import boto3
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context):

    logging.info(json.dumps(event))

    # 後で削除
    return json.loads(event["body"])["challenge"]

    client = boto3.client('lambda')
    response = client.invoke(
        FunctionName='chatGPT',
        InvocationType='Event',
        LogType='Tail',
        Payload= json.dumps(event)
    )

    return {
        'statusCode': 200,
        'body': json.dumps('OK')
    }
