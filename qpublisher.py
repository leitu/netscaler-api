#!/usr/bin/env python -B

import logging
import pika
import sys
import json

LOGGER = logging.getLogger("QPublisher")

class QPublisher(object):
    """
    Basic RabbitMQ publisher class
    """

    def __init__(self, rmq_url, msg_queue="", exchange="", routing_key=""):
        """Setup the publisher object, passing in the URL we will use
        to connect to RabbitMQ.
        """
        self.msg_queue = msg_queue
        self.exchange = exchange
        self.routing_key = routing_key
        self.rmq_url = rmq_url


        # Initialize the connection
        self.connection = pika.BlockingConnection(pika.URLParameters(self.rmq_url))
        self.channel = self.connection.channel()
        self.channel.queue_declare(queue=self.msg_queue, durable=True)


    def send_str_message(self, payload):
        self.channel.basic_publish(exchange=self.exchange, routing_key=self.routing_key, body=payload)
        self.connection.close()



