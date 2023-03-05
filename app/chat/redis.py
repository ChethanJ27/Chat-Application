import redis
import json


pool = redis.ConnectionPool(host='redis', port=6379, db=0)
redis_conn = redis.Redis(connection_pool=pool)
pubsub = redis_conn.pubsub()

# Publisher
def publish_to_channel(channel, message):
    redis_conn.publish(channel, message)

def handle_message(channel, message):
    # Parse the message to extract the data you need
    # In this case, assume the message is a JSON string
    data = json.loads(message)
    print(data)
    from .consumers import ChatConsumer
    # Create a new instance of ChatConsumer and call its receive method
    # passing the data from the message
    consumer = ChatConsumer()
    consumer.user = data['user']
    consumer.room_group_name = data['room_group_name']
    consumer.receive(text_data=data['message'])

pubsub.subscribe('my_channel')
for message in pubsub.listen():
    handle_message(message['channel'], message['data'])
