"""
Unit tests for Asynchronous Message Queue broker and Consumer Worker in Person 3.
"""
import sys
from pathlib import Path
import pytest
import time

ROOT = Path(__file__).resolve().parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
P3_PATH = Path(__file__).resolve().parent.parent
if str(P3_PATH) not in sys.path:
    sys.path.insert(0, str(P3_PATH))

try:
    from Person_3.message_queue.queue_broker import MessageQueueBroker
    from Person_3.message_queue.consumer_worker import ConsumerWorker
except ImportError:
    from message_queue.queue_broker import MessageQueueBroker
    from message_queue.consumer_worker import ConsumerWorker

def test_queue_publish_and_retrieve():
    broker = MessageQueueBroker()
    msg_id = broker.publish(
        topic="disputes.incoming",
        payload={"complaint_text": "I suspect unauthorized card charges", "transaction_id": "TX1001"}
    )
    assert msg_id is not None
    assert broker.get_queue_length() >= 1

    msg = broker.consume(block=False)
    assert msg is not None
    assert (msg.get("msg_id") or msg.get("message_id")) == msg_id
    assert msg["payload"]["complaint_text"] == "I suspect unauthorized card charges"

def test_consumer_worker_execution():
    broker = MessageQueueBroker()
    worker = ConsumerWorker(broker=broker, auto_start=False)

    # Publish a job
    msg_id = broker.publish(
        topic="disputes.incoming",
        payload={"complaint_text": "Unknown debit of $200", "transaction_id": "TX1002"}
    )

    # Process one job synchronously
    result = worker.process_one_now()
    assert result is not None
    assert result.get("transaction_id") == "TX1002"
    assert worker.processed_count >= 1
