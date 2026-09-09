import dramatiq
from dramatiq.brokers.rabbitmq import RabbitmqBroker

from app.core.config import get_settings

broker = RabbitmqBroker(url=get_settings().rabbitmq_url)

dramatiq.set_broker(broker)
