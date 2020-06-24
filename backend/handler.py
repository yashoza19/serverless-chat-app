import json
import logging
import boto3
import time

logger = logging.getLogger("handler_logger")
logger.setLevel(logging.DEBUG)

dynamodb = boto3.resource("dynamodb")


def _get_body(event):
    try:
        return json.loads(event.get("body", ""))
    except:
        logger.debug("event body could not be JSON decoded.")
        return {}


def _get_response(status_code, body):
    if not isinstance(body, str):
        body = json.dumps(body)
    return {"statusCode": status_code, "body": body}


def _send_to_connection(connection_id, data, event):
    gatewayapi = boto3.client("apigatewaymanagementapi",
            endpoint_url = "https://" + event["requestContext"]["domainName"] +
                    "/" + event["requestContext"]["stage"])
    return gatewayapi.post_to_connection(ConnectionId=connection_id,
            Data=json.dumps(data).encode('utf-8'))

def connection_manager(event, context):
    connectionID = event["requestContext"].get("connectionId")
    
    if event["requestContext"]["eventType"] == "CONNECT":
        logger.info("Connect requested")

        # Add connectionID to the database
        table = dynamodb.Table("serverless-chat_Connections")
        table.put_item(Item={"ConnectionID": connectionID})
        return _get_response(200, "Connect successful.")

    elif event["requestContext"]["eventType"] == "DISCONNECT":
        logger.info("Disconnect requested")

        # Remove the connectionID from the database
        table = dynamodb.Table("serverless-chat_Connections")
        table.delete_item(Key={"ConnectionID": connectionID})
        return _get_response(200, "Disconnect successful.")

    else:
        logger.error("Connection manager received unrecognized eventType '{}'")
        return _get_response(500, "Unrecognized eventType.")


def default_message(event, context):
    """
    Send back error when unrecognized WebSocket action is received.
    """
    logger.info("Unrecognized WebSocket action received.")
    return _get_response(400, "Unrecognized WebSocket action.")


def get_recent_messages(event, context):
    """
    Return the 10 most recent chat messages.
    """
    connectionID = event["requestContext"].get("connectionId")
    logger.info("Retrieving most recent messages for CID '{}'"\
            .format(connectionID))

    if not connectionID:
        logger.error("Failed: connectionId value not set.")
        return _get_response(500, "connectionId value not set.")

    table = dynamodb.Table("serverless-chat_Messages")
    response = table.query(KeyConditionExpression="Room = :room",
            ExpressionAttributeValues={":room": "general"},
            Limit=10, ScanIndexForward=False)
    items = response.get("Items", [])

    messages = [{"username": x["Username"], "content": x["Content"]}
            for x in items]
    messages.reverse()

    data = {"messages": messages}
    _send_to_connection(connectionID, data, event)

    return _get_response(200, "Sent recent messages to '{}'."\
            .format(connectionID))


def send_message(event, context):
    logger.info("Message sent on WebSocket.")
    body = _get_body(event)
    for attribute in ["username", "content"]:
        if attribute not in body:
            logger.debug("Failed: '{}' not in message dict."\
                    .format(attribute))
            return _get_response(400, "'{}' not in message dict"\
                    .format(attribute))
    table = dynamodb.Table("serverless-chat_Messages")
    response = table.query(KeyConditionExpression="Room = :room",
            ExpressionAttributeValues={":room": "general"},
            Limit=1, ScanIndexForward=False)
    items = response.get("Items", [])
    index = items[0]["Index"] + 1 if len(items) > 0 else 0

    timestamp = int(time.time())
    username = body["username"]
    content = body["content"]
    table.put_item(Item={"Room": "general", "Index": index,
            "Timestamp": timestamp, "Username": username,
            "Content": content})

    table = dynamodb.Table("serverless-chat_Connections")
    response = table.scan(ProjectionExpression="ConnectionID")
    items = response.get("Items", [])
    connections = [x["ConnectionID"] for x in items if "ConnectionID" in x]
    logger.debug(connections)

    message = {"username": username, "content": content}
    logger.debug("Broadcasting message: {}".format(message))
    data = {"messages": [message]}
    for connectionID in connections:
        logger.debug("here")
        _send_to_connection(connectionID, data, event)
    return _get_response(200, "Message sent to all connections.")

def ping(event, context):
    logger.info("Ping requested.")
    return _get_response(200, "PONG!")