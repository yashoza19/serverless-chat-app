import json
import logging
import boto3
import time

logger = logging.getLogger("handler_logger")
logger.setLevel(logging.DEBUG)

dynamodb = boto3.resource("dynamodb")


def ping(event, context):

    logger.info("Ping requested.")

    table = dynamodb.Table("serverless-chat_Messages")
    timestamp = int(time.time())
    table.put_item(Item={"Room":"general","Index": 0, "Timestamp":timestamp, "Username":"ping-user","Content":"PING!"})
    logger.info("Item added to the database-Messages")
    response = {
        "statusCode": 200,
        "body": "PONG!"
    }

    return response