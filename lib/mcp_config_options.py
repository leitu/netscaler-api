# This class reads the mcp configuration and sets MCP default configuration options
import ConfigParser, os, logging

LOGGER = logging.getLogger("mcp_config_options")

class MCPConfigParser:
    def __init__(self, config_file):
        if not os.path.exists(config_file):
            raise IOError('Unable to access configuration {}'.format(config_file))

        # Section in the following list are mandatory. Throw exception is any of them
        # is missing.
        config_sections = ["mcp_worker", "rabbitmq_consumer", "rabbitmq_publisher"]
        config = ConfigParser.ConfigParser()
        config.read(config_file)
        for section in config_sections:
            if section not in config.sections():
                raise ConfigParser.NoSectionError(section)
        self.config_data = config

    def mcp_worker_opts(self):
        # set default threads value if it is not defined
        if "max_threads" not in self.config_data.options("mcp_worker"):
            threads = 1
        else:
            try:
                threads = int(self.config_data.get("mcp_worker", "max_threads"))
                if threads < 1:
                    raise ValueError
            except ValueError:
                LOGGER.error("threads must be a number greater than 0")
                raise ValueError("threads must be a number greater than 0")
        return {"max_threads":threads}

    def rabbit_mq_opts(self, section):
        # type is consumer or publisher section
        rabbit_mq_opts_dict = {}
        # mandatory options
        mandatory_items = ["username", "password", "host", "queue"]
        for mandatory_item in mandatory_items:
            if mandatory_item not in self.config_data.options(section):
                raise ConfigParser.NoOptionError(mandatory_item)
            else:
                rabbit_mq_opts_dict[mandatory_item] = self.config_data.get(section, mandatory_item)
        if "exchange" not in self.config_data.options(section):
            rabbit_mq_opts_dict["exchange"] = ""
        else:
            rabbit_mq_opts_dict["exchange"] = self.config_data.get(section, "exchange")

        if "port" not in self.config_data.options(section):
            rabbit_mq_opts_dict["port"] = "5672"
        else:
            rabbit_mq_opts_dict["port"] = self.config_data.get(section, "port")

        if "routing_key" not in self.config_data.options(section):
            # if routing key is not defined use queue as default routing key
            rabbit_mq_opts_dict["routing_key"] = self.config_data.get(section, "queue")
        else:
            rabbit_mq_opts_dict["routing_key"] = self.config_data.get(section, "routing_key")

        return rabbit_mq_opts_dict

    def construct_rabbitmq_url(self, type):
        # return rabbitmq connnection url based on type (consumer or publisher)
        if type == "consumer":
            url_data = self.rabbit_mq_opts("rabbitmq_consumer")
        elif type == "publisher":
            url_data = self.rabbit_mq_opts("rabbitmq_publisher")
        else:
            raise ValueError("Unknown rabbitmq type")
        return "amqp://{}:{}@{}:{}/".format(url_data['username'], url_data['password'],
                                           url_data['host'], url_data['port'])
