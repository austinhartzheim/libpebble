import sys
import logging
from websocket import *
from struct import unpack

# This file contains the libpebble websocket client.
# Based on websocket.py from:
# https://github.com/liris/websocket-client

class WebSocketPebble(WebSocket):

######## libPebble Bridge Methods #########

    def write(self, payload, opcode = ABNF.OPCODE_BINARY):
        """
        BRIDGES THIS METHOD:
        def write(self, message):
            try:
                self.send_queue.put(message)
                self.bt_message_sent.wait()
            except:
                self.bt_teardown.set()
                if self.debug_protocol:
                    log.debug("LightBlue process has shutdown (queue write)")

        """
        frame = ABNF.create_frame(payload, opcode)
        if self.get_mask_key:
            frame.get_mask_key = self.get_mask_key
        data = frame.format()
        self.io_sock.send(data)
        if traceEnabled:
            logging.debug('send>>> ' + data.encode('hex'))

    def read(self):
        """
        BRIDGES THIS METHOD:
        def read(self):
            try:
                return self.rec_queue.get()
            except Queue.Empty:
                return (None, None, '')
            except:
                self.bt_teardown.set()
                if self.debug_protocol:
                    log.debug("LightBlue process has shutdown (queue read)")
                return (None, None, '')
        """
        try:
            opcode, data = self.recv_data()
            size, endpoint = unpack("!HH", data[1:5])
            resp = data[5:]
            direction = unpack('!b',data[0])
            if direction[0]==3:
                logging.debug("Server: %s" % repr(data[1:]))
            if direction[0]==2:
                logging.debug("Log: %s" % repr(data[1:]))
            if direction[0]==1:
                logging.debug("Phone ==> Watch: %s" % data[1:].encode("hex"))
            if direction[0]==0:
                logging.debug("Watch ==> Phone: %s" % data[1:].encode("hex"))
                return (endpoint, resp, data[1:5])
            else:
                return (None, None, data)
        except:
            pass # supressing warnings upon disconnection



######################################

def create_connection(url, timeout=None, **options):
    """
    connect to url and return websocket object.

    Connect to url and return the WebSocket object.
    Passing optional timeout parameter will set the timeout on the socket.
    If no timeout is supplied, the global default timeout setting returned by getdefauttimeout() is used.
    You can customize using 'options'.
    If you set "header" dict object, you can set your own custom header.

    >>> conn = create_connection("ws://echo.websocket.org/",
         ...     header=["User-Agent: MyProgram",
         ...             "x-custom: header"])


    timeout: socket timeout time. This value is integer.
             if you set None for this value, it means "use default_timeout value"

    options: current support option is only "header".
             if you set header as dict value, the custom HTTP headers are added.
    """

    sockopt = options.get("sockopt", ())
    websock = WebSocketPebble(sockopt=sockopt) #changed this to WebSocketPebble
    websock.settimeout(timeout != None and timeout or default_timeout)
    websock.connect(url, **options)
    return websock

_MAX_INTEGER = (1 << 32) -1
_AVAILABLE_KEY_CHARS = range(0x21, 0x2f + 1) + range(0x3a, 0x7e + 1)
_MAX_CHAR_BYTE = (1<<8) -1




if __name__ == "__main__":
    enableTrace(True)
    if len(sys.argv) < 2:
        print "Need the WebSocket server address, i.e. ws://localhost:9000"
        sys.exit(1)
    ws = create_connection(sys.argv[1])
    print("Sending 'Hello, World'...")
    ws.send("Hello, World")
    print("Sent")
    print("Receiving...")
    result = ws.recv()
    print("Received '%s'" % result)
