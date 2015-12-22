import sys, os, time, atexit, logging
from signal import SIGTERM

LOGGER = logging.getLogger("Daemon")

class Daemon:
    """
    A generic daemon class.

    Usage: subclass the daemon class and override the run() method.
    Works on python 2.7.x
    """

    def __init__(self, pidfile, config_data="", stdin="/dev/null", stdout="/dev/null", stderr="/dev/null"):
        self.stdin = stdin
        self.stdout = stdout
        self.stderr = stderr
        self.pidfile = pidfile
        self.config_data = config_data


    def daemonize(self):
        """
        Method for unix double-fork (Per Advanced programming in the UNIX Environment book)
        Fork a second child and exit immediately to prevent zombies.  This
        causes the second child process to be orphaned, making the init
        process responsible for its cleanup.  And, since the first child is
        a session leader without a controlling terminal, it's possible for
        it to acquire one by opening a terminal in the future (System V-
        based systems).  This second fork guarantees that the child is no
        longer a session leader, preventing the daemon from ever acquiring
        a controlling terminal.
        """
        try:
            pid = os.fork()
            if pid > 0:
                # exit the parent
                sys.exit(0)
        except OSError, e:
            sys.stderr.write("fork #1 failed {} {}").format(e.errno, e.strerror)
            LOGGER.error("fork #1 failed {} {}".format(e.errno, e.strerror))
            sys.exit(1)

        # Decouple from parent environment
        os.chdir("/")
        os.setsid()
        os.umask(0)

        # second fork
        try:
            pid = os.fork()
            if pid > 0:
                # exit the parent
                sys.exit(0)
        except OSError, e:
            sys.stderr.write("fork #2 failed {} {}").format(e.errno, e.strerror)
            LOGGER.error("fork #2 failed {} {}".format(e.errno, e.strerror))
            sys.exit(1)

        # redirect standard file descriptors
        sys.stdout.flush()  # forces immediate write
        sys.stderr.flush()
        si = file(self.stdin, 'r')
        so = file(self.stdout, 'a+')
        se = file(self.stderr, 'a+', 0)
        os.dup2(si.fileno(), sys.stdin.fileno())
        os.dup2(so.fileno(), sys.stdout.fileno())
        os.dup2(se.fileno(), sys.stderr.fileno())

        # write pidfile
        atexit.register(self.delpid)
        pid = str(os.getpid())
        file(self.pidfile, 'w+').write("{}".format(pid))
        LOGGER.info("Daemon created with pid {}".format(pid))

    def delpid(self):
        """
        Remove pid file
        """
        os.remove(self.pidfile)
        LOGGER.info("Removed pidfile at {}".format(self.pidfile))

    def start(self):
        """
        Start the daemon
        """
        # Check for pidfile to see if the daemon already runs"
        try:
            pf = file(self.pidfile, 'r')
            pid = int(pf.read().strip())
            pf.close()
        except IOError:
            pid = None

        if pid:
            message = "pidfile {} already exists. Deamon possibly running.\n".format(self.pidfile)
            sys.stderr.write("{}".format(message))
            sys.exit(1)

        # Start the daemon
        self.daemonize()
        self.run()
        LOGGER.info("Daemon started...")

    def stop(self):
        """
        Stop the daemon
        """
        # Get pid from pidfile
        try:
            pf = file(self.pidfile, 'r')
            pid = int(pf.read().strip())
            pf.close()
        except IOError:
            pid = None

        if not pid:
            message = "pidfile {} does not  exist. Daemon possibly not running.\n".format(self.pidfile)
            sys.stderr.write("{}".format(message))
            return

        # Attempt to kill the process
        try:
            while 1:
                os.kill(pid, SIGTERM)
                time.sleep(0.1)
                LOGGER.info("Daemon stopped...")
        except OSError, e:
            e = str(e)
            if e.find("No such process") > 0:
                if os.path.exists(self.pidfile):
                    os.remove(self.pidfile)
            else:
                print(str(e))
                sys.exit(1)

    def restart(self):
        """
        Restart the daemon
        """
        self.stop()
        self.start()

    def run(self):
        """
        You should override this method when you subclass Daemon. It will be called after the process has been
        daemonized by start() or restart().
        """
