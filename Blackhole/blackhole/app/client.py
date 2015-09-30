# -*- coding: utf-8 -*-
import logging
import pty
import shlex
import termios
import socket
import signal
import tty
import sys
import select
import os

import paramiko

TIME_OUT = 3

logger = logging.getLogger("blackhole.client")


# Clients
class Client(object):

    def __init__(self, session):
        self._session = session

class SecureShellClient(Client):

    def __init__(self, session):
        super(SecureShellClient, self).__init__(session)
        self._socket = None
        logger.debug(u"Client Created")

    def connect(self, ip, port, size):
        self._size = size
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.settimeout(TIME_OUT)
        self._socket.connect((ip, port))
        logger.debug(u"Connected to %s:%s" % (ip, port))

    def get_transport(self):
        transport = paramiko.Transport(self._socket)
        transport.set_keepalive(30)
        transport.start_client()
        return transport

    def start_session_using_pk(self, user, private_key):
        logger.debug(u"Validating with Private Key")
        transport = None
        try:
            transport = self.get_transport()
            transport.auth_publickey(user, private_key)
            self._start_session(transport)
        except Exception as e:
            logger.error(e.message)
            self._session.close_session()
            if transport:
                transport.close()
            self._socket.close()
            raise e

    def start_session_using_password(self, user, password):
        logger.debug(u"Validating with Password")
        transport = None
        try:
            transport = self.get_transport()
            transport.auth_password(user, password)
            self._start_session(transport)
        except Exception as e:
            logger.error(e.message)
            self._session.close_session()
            if transport:
                transport.close()
            self._socket.close()
            raise paramiko.AuthenticationException(u"Invalid Password")

    def _start_session(self, transport):
        chan = transport.open_session()
        cols, rows = self._size
        chan.get_pty('xterm', cols, rows)
        chan.invoke_shell()
        self.interactive_shell(chan)
        chan.close()
        self._session.close_session()
        transport.close()
        self._socket.close()

    def interactive_shell(self, chan):
        sys.stdout.flush()
        try:
            signal.signal(signal.SIGHUP, self._session.kill_session)
            oldtty = termios.tcgetattr(sys.stdin)
            tty.setraw(sys.stdin.fileno())
            tty.setcbreak(sys.stdin.fileno())
            chan.settimeout(0.0)
            while True:
                r, w, e = select.select([chan, sys.stdin], [], [])
                if chan in r:
                    try:
                        x = chan.recv(1024)
                        if len(x) == 0:
                            break
                        sys.stdout.write(x)
                        sys.stdout.flush()
                    except socket.timeout:
                        break
                if sys.stdin in r:
                    x = os.read(sys.stdin.fileno(), 1)
                    if len(x) == 0:
                        break
                    chan.send(x)
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, oldtty)
        except Exception as e:
            logger.error(e.message)
            raise e


class DBClient(Client):

    def __init__(self, session):
        super(DBClient, self).__init__(session)
        logger.debug(u"Client Created")

    def connect(self, ip, port, size):
        self._size = size
        logger.debug(u"Connected to %s:%s" % (ip, port))

    def start_session(self):
        logger.debug(u"Validating with Password")
        try:
            self._start_session()
        except Exception as e:
            logger.error(e.message)
            self._session.close_session()
            raise e

    def _start_session(self):
        signal.signal(signal.SIGHUP, self._session.kill_session)
        sys.stdout.flush()
        pty.spawn(shlex.split(self._session.get_cmd()), sys.stdout.read)


