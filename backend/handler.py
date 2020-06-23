import json
import logging

logger = logging.getLogger("handler_logger")
logger.setLevel(logging.DEBUG)


def ping(event, context):

    logger.info("Ping requested.")
    response = {
        "statusCode": 200,
        "body": "PONG!"
    }

    return response

    # Use this code if you don't use the http event with the LAMBDA-PROXY
    # integration
    """
    return {
        "message": "Go Serverless v1.0! Your function executed successfully!",
        "event": event
    }
    """
