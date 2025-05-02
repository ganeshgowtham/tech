from typing import Dict, List, Callable, Any
import threading
from datetime import datetime
from queue import Queue
import uuid

class MessageBroker:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(MessageBroker, cls).__new__(cls)
                cls._instance._initialize()
            return cls._instance

    def _initialize(self):
        self.subscribers: Dict[str, List[Callable]] = {}
        self.messages: Dict[str, Queue] = {}
        self.store: Dict[str, Dict[str, Dict[str, Any]]] = {}

    def subscribe(self, topic: str, callback: Callable):
        """Subscribe to a topic with a callback function"""
        if topic not in self.subscribers:
            self.subscribers[topic] = []
            self.messages[topic] = Queue()
        self.subscribers[topic].append(callback)

    def unsubscribe(self, topic: str, callback: Callable):
        """Unsubscribe from a topic"""
        if topic in self.subscribers:
            self.subscribers[topic].remove(callback)

    def publish(self, topic: str, message: Dict[str, Any]):
        """
        Publish a message to a topic
        Args:
            topic: The topic to publish to
            message: Dictionary containing the message data
        """
        if topic not in self.store:
            self.store[topic] = {}
        
        msg_id = str(uuid.uuid4())
        msg_data = {
            'id': msg_id,
            'content': message,
            'timestamp': datetime.now().isoformat(),
            'topic': topic
        }
        
        self.store[topic][msg_id] = msg_data
        
        # Notify all subscribers
        if topic in self.subscribers:
            for callback in self.subscribers[topic]:
                callback(msg_data)

        return msg_id

def producer(message: Dict[str, Any], topic: str = "default") -> str:
    """
    Produces a message to the specified topic.
    Args:
        message: Dictionary containing the message data
        topic: The topic to publish to
    Returns:
        The message ID
    """
    broker = MessageBroker()
    return broker.publish(topic, message)

def consumer(callback: Callable[[Dict[str, Any]], None], topic: str = "default"):
    """
    Subscribes to messages on the specified topic.
    Args:
        callback: Function that will be called with the message dictionary
        topic: The topic to subscribe to
    """
    broker = MessageBroker()
    broker.subscribe(topic, callback)

# Example usage:
if __name__ == "__main__":
    def message_handler(message):
        content = message['content']
        print('content', content['type'])
        match content['type']:
            case "chat_console":
                print(f"Chat Console Message: {message}")
            case "notifications":
                print(f"Notification: {message}")
            case _:
                print(f"Other message: {message}")

    # Subscribe to messages
    consumer(message_handler)

    # Produce some messages with dictionary content
    msg_id = producer({"type": "chat_console", "text": "Hello, World!", "priority": "high"})
    msg_id2 = producer({"type": "notifications", "text": "Status update", "status": "success"})

    # Can also use different topics
    consumer(message_handler, "notifications")
    producer({"type": "alert", "text": "New notification!", "urgency": "medium"}, "notifications")