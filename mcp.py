#!/usr/bin/env python -B

import sys, logging.config, json, Queue, logging, time, argparse
from lib import daemon, worker, mcp_config_options

LOGGER = logging.getLogger("MCP")


class MCPDaemon(daemon.Daemon):
    def run(self):
        thread_queue = Queue.Queue()
        worker_opts = self.config_data.mcp_worker_opts()
        mq_url = self.config_data.construct_rabbitmq_url('consumer')
        try:
            max_threads = worker_opts['max_threads']
        except:
            max_threads = 1

        if max_threads < 1:
            max_threads = 1

        while True:
            time.sleep(1)
            LOGGER.debug("Max threads: {}".format(max_threads))
            if thread_queue.qsize() < max_threads:
                worker_thread = worker.WorkerThread(thread_queue, mq_server_url=mq_url, config_data=self.config_data)
                worker_thread.start()
                LOGGER.debug("Thread QSize: {}".format(thread_queue.qsize()))
            else:
                LOGGER.debug("Waiting for threads to finish. QSize: {}".format(thread_queue.qsize()))


if __name__ == "__main__":
    try:
        with open('mcp_logger.json', 'rt') as f:
            logger_config = json.load(f)
        logging.config.dictConfig(logger_config)
    except:
        sys.stderr.write("Unable to read logger configuration\n")
        exit(1)

    # TODO: Future iteration add deamoninze argument (-d or --daemonize). Without it the program
    # TODO: should display information in stdout.
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--start", help="start the MCP daemon", action="store_true", default=False)
    parser.add_argument("-k", "--kill", help="kill the MCP daemon", action="store_true", default=False)
    parser.add_argument("-c", "--config", help="path to configuration file", default="mcp.cfg")
    parser.add_argument("-p", "--pid", help="path to pid file", default="/tmp/mcp.pid")
    args = parser.parse_args()

    if len(sys.argv) == 1:
        parser.print_help()
        exit(1)

    if args.start == True and args.kill == True:
        sys.stderr.write("Can't set start and kill arguments\n")
        exit(1)

    if args.start == False and args.kill == False:
        sys.stderr.write("You must set start (-s) or kill (-k) argument\n")
        exit(1)

    try:
        config_opts = mcp_config_options.MCPConfigParser(args.config)
    except Exception as e:
        LOGGER.error("Unable to parse config: {}".format(e))
        exit(1)

    daemon = MCPDaemon(args.pid, config_opts)

    if args.start:
        daemon.start()
    elif args.kill:
        daemon.stop()
    else:
        sys.stderr.write("Unknown command")
        parser.print_help()
        sys.exit(1)
