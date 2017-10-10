#!/usr/bin/env python

"""
Run a multi-threaded single-client SCPI Server implemented in Python.

Using a single-client server is sensible for many SCPI servers
where state would need to be shared between the multiple clients
and thus access to it would need to be made thread-safe.
In most cases, this doesn't make sense. Everything is
simply much easier when allowing only one client at a time.

The design choice for a multi-threaded server was made in
order to be able to actively disconnect additional clients
while another one is already connected.

Contains code from https://gist.github.com/pklaus/db709c8c1279348e0638
"""

# Make it work on Python 2 and Python 3:
try:
    import socketserver
except ImportError:
    import SocketServer as socketserver
import socket, threading
import argparse, random, logging
from logging import DEBUG, INFO, WARNING, ERROR, CRITICAL

logger = logging.getLogger('scpi-server')

class CmdTCPServer(socketserver.ThreadingTCPServer):
    """
    A TCP server made to respond to line based commands.
    """

    #: newline character(s) to be added to string responses
    newline = '\n'
    #: Ctrl-C will cleanly kill all spawned threads
    daemon_threads = True
    #: much faster rebinding possible
    allow_reuse_address = True
    address_family = socket.AF_INET6

    class CmdRequestHandler(socketserver.StreamRequestHandler):
        def handle(self):
            if not self.server.lock.acquire(blocking=False):
                self.log(DEBUG, 'An additional cliend tried to connect from {client}. Denying...')
                return
            self.log(DEBUG, 'Connected to {client}.')
            try:
                while True:
                    self.single_cmd()
            except Disconnected:
                pass
                self.log(DEBUG, 'The client {client} closed the connection')
            finally:
                self.server.lock.release()
        def read_cmd(self):
            return self.rfile.readline().decode('utf-8').strip()
        def log(self, level, msg, *args, **kwargs):
            if type(level) == str:
                level = getattr(logging, level.upper())
            msg = msg.format(client=self.client_address[0])
            logger.log(level, msg, *args, **kwargs)
        def send_reply(self, reply):
            if type(reply) == str:
                if self.server.newline: reply += self.server.newline
                reply = reply.encode('utf-8')
            self.wfile.write(reply)
        def single_cmd(self):
            cmd = self.read_cmd()
            if not cmd: raise Disconnected
            self.log(DEBUG, 'Received a cmd: {}'.format(cmd))
            try:
                reply = self.server.process(cmd)
                if reply is not None:
                    self.send_reply(reply)
            except:
                self.send_reply('ERR')

    def __init__(self, server_address, name=None):
        socketserver.TCPServer.__init__(self, server_address, self.CmdRequestHandler)
        self.lock = threading.Lock()
        self.name = name if name else "{}:{}".format(*server_address)

    def process(self, cmd):
        """
        Implement this method to handle command processing.
        For each command, this method will be called.
        Return a string or bytes as appropriate.
        If your the message is only a command (not a query), return None.
        """
        raise NotImplemented

class SCPIServerExample(CmdTCPServer):

    def process(self, cmd):
        """
        This is the method to process each SCPI command
        received from the client.
        """
        if cmd.startswith('*IDN?'):
            return self.name
        if cmd.startswith('READ?'):
            return '{:+.6E}'.format(random.random())
        else:
            return 'unknown cmd'

def main():
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[1])
    parser.add_argument('--port', type=int, default=5025, help='TCP port to listen to.')
    parser.add_argument('--host', default='::', help='The host / IP address to listen at.')
    parser.add_argument('--loglevel', default='INFO', help='log level',
        choices=['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG'])
    args = parser.parse_args()
    logging.basicConfig(format='%(message)s', level=args.loglevel.upper())
    scpi_server = SCPIServerExample((args.host, args.port))
    try:
        scpi_server.serve_forever()
    except KeyboardInterrupt:
        logger.info('Ctrl-C pressed. Shutting down...')
    scpi_server.server_close()

class Disconnected(Exception): pass

if __name__ == "__main__":
    main()
