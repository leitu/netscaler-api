import threading, logging, time, Queue, uuid, json, collections
import netscaler
from qconsumer import QConsumer
from qpublisher import QPublisher
from redismanager import RedisManager

LOGGER = logging.getLogger("WorkerThread")


class WorkerThread(threading.Thread):
    """
    Worker thread management class
    """

    def __init__ (self, thread_queue, mq_server_url="", config_data=""):
        """
        Initializer of the WorkerThread class
        :param thread_queue: Queue that this class will communicate with the main thread
        :param mq_server_addr: RabbitMQ server address in format "<protocol>://username:password@host:port"
        """
        threading.Thread.__init__(self)
        self.worker_id = "worker-{}".format(str(uuid.uuid4()))
        self.mq_server_url = mq_server_url
        self.payload = None
        self.thread_queue = thread_queue
        self.worker_queue = Queue.Queue()
        self.rabbitmq_publisher_data = config_data.rabbit_mq_opts('rabbitmq_publisher')
        self.rabbitmq_publisher_url = config_data.construct_rabbitmq_url('publisher')
        self.rm = RedisManager("gspanos-genserver01.tr1.bbstack.net")

    def run(self):
        """
        Run the worker. Communication between RabbitMQ consumer class and this worker is done
        via Queue. When the job is done we kill the thread.
        """
        LOGGER.debug("{} Initialized".format(self.worker_id))
        self.thread_queue.put("worker-{} waiting".format(self.worker_id))
        message_consumer = QConsumer(self.worker_queue, self.mq_server_url)
        message_consumer.run()
        payload = self.worker_queue.get()
        LOGGER.info("Raw Payload: {}".format(payload))
        data = json.loads(payload, object_pairs_hook=collections.OrderedDict)
        LOGGER.info("Data: {}".format(data))
        try:
            netscaler_task = netscaler.Load(data)
            result = netscaler_task.run()
            #returned_data = json.dumps(str(result), sort_keys=False)
            returned_data = result
            LOGGER.info("{}: Payload {}".format(self.worker_id, data))
        except Exception as e:
            returned_data = str(e)
            LOGGER.info("{} exception: Payload {}".format(self.worker_id, e))
        try:
            publisher = QPublisher(self.rabbitmq_publisher_url, msg_queue=self.rabbitmq_publisher_data['queue'],
                   exchange=self.rabbitmq_publisher_data['exchange'],
                   routing_key=self.rabbitmq_publisher_data['routing_key'])
            publisher.send_str_message(returned_data)
            LOGGER.info("Returned data: {}".format(returned_data))
            LOGGER.info("Repr data: {}".format(repr(returned_data)))
        except Exception as e:
            LOGGER.error("Error publishing: {}".format(e))
        self.thread_queue.task_done()
        self.thread_queue.get()
        LOGGER.debug("{} Terminated".format(self.worker_id))
        exit(0)





