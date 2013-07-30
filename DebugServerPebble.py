import sys
from twisted.internet import reactor
from twisted.python import log
from twisted.web.server import Site
from twisted.web.static import File
from autobahn.websocket import *



class EchoServerProtocol(WebSocketServerProtocol):
   peers = [];
   transports = {}   
   
   def makeConnection(self, transport):
       """Make a connection to a transport and a server.

       This sets the 'transport' attribute of this Protocol, and calls the
       connectionMade() callback.
       """
       self.connected = 1
       self.transport = transport
       self.transports[transport.getPeer().host+":"+str(transport.getPeer().port)]=transport
       self.connectionMade()

   
   def sendData(self, data, sync = False, chopsize = None, peer=None):

     if chopsize and chopsize > 0:
        i = 0
        n = len(data)
        done = False
        while not done:
           j = i + chopsize
           if j >= n:
              done = True
              j = n
           self.send_queue.append((data[i:j], True))
           i += chopsize
        self._trigger()
     else:
        if sync or len(self.send_queue) > 0:
           self.send_queue.append((data, sync))
           self._trigger()
        else:
           if peer:
               self.transport = self.transports[peer] #switch to custom peer  
           self.transport.write(data)
           if self.logOctets:
              self.logTxOctets(data, False)



   def sendFrame(self, opcode, payload = "", fin = True, rsv = 0, mask = None, payload_len = None, chopsize = None, sync = False, peer = None):

      if self.websocket_version == 0:
         raise Exception("function not supported in Hixie-76 mode")

      if payload_len is not None:
         if len(payload) < 1:
            raise Exception("cannot construct repeated payload with length %d from payload of length %d" % (payload_len, len(payload)))
         l = payload_len
         pl = ''.join([payload for k in range(payload_len / len(payload))]) + payload[:payload_len % len(payload)]
      else:
         l = len(payload)
         pl = payload

      ## first byte
      ##
      b0 = 0
      if fin:
         b0 |= (1 << 7)
      b0 |= (rsv % 8) << 4
      b0 |= opcode % 128

      ## second byte, payload len bytes and mask
      ##
      b1 = 0
      if mask or (not self.isServer and self.maskClientFrames) or (self.isServer and self.maskServerFrames):
         b1 |= 1 << 7
         if not mask:
            mask = struct.pack("!I", random.getrandbits(32))
            mv = mask
         else:
            mv = ""

         ## mask frame payload
         ##
         if l > 0 and self.applyMask:
            masker = createXorMasker(mask, l)
            plm = masker.process(pl)
         else:
            plm = pl

      else:
         mv = ""
         plm = pl

      el = ""
      if l <= 125:
         b1 |= l
      elif l <= 0xFFFF:
         b1 |= 126
         el = struct.pack("!H", l)
      elif l <= 0x7FFFFFFFFFFFFFFF:
         b1 |= 127
         el = struct.pack("!Q", l)
      else:
         raise Exception("invalid payload length")

      raw = ''.join([chr(b0), chr(b1), el, mv, plm])

      if self.logFrames:
         frameHeader = FrameHeader(opcode, fin, rsv, l, mask)
         self.logTxFrame(frameHeader, payload, payload_len, chopsize, sync)

      ## send frame octets
      ##
      self.sendData(raw, sync, chopsize,peer)

   def sendMessage(self, payload, binary = False, payload_frag_size = None, sync = False, peer=None):

      if self.trackedTimings:
         self.trackedTimings.track("sendMessage")
      if self.state != WebSocketProtocol.STATE_OPEN:
         return
      if self.websocket_version == 0:
         if binary:
            raise Exception("cannot send binary message in Hixie76 mode")
         if payload_frag_size:
            raise Exception("cannot fragment messages in Hixie76 mode")
         self.sendMessageHixie76(payload, sync, peer)
      else:

         self.sendMessageHybi(payload, binary, payload_frag_size, sync, peer = peer)


   def sendMessageHixie76(self, payload, sync = False, peer = None):
      """
      Hixie76-Variant of sendMessage().

      Modes: Hixie
      """
      self.sendData('\x00' + payload + '\xff', sync = sync, peer = peer)


   def sendMessageHybi(self, payload, binary = False, payload_frag_size = None, sync = False, peer = None):
      """
      Hybi-Variant of sendMessage().

      Modes: Hybi
      """

      ## (initial) frame opcode
      ##
      if binary:
         opcode = 2
      else:
         opcode = 1

      ## explicit payload_frag_size arguments overrides autoFragmentSize setting
      ##
      if payload_frag_size is not None:
         pfs = payload_frag_size
      else:
         if self.autoFragmentSize > 0:
            pfs = self.autoFragmentSize
         else:
            pfs = None

      ## send unfragmented
      ##
      if pfs is None or len(payload) <= pfs:
         self.sendFrame(opcode = opcode, payload = payload, sync = sync, peer=peer)

      ## send data message in fragments
      ##
      else:
         if pfs < 1:
            raise Exception("payload fragment size must be at least 1 (was %d)" % pfs)
         n = len(payload)
         i = 0
         done = False
         first = True
         while not done:
            j = i + pfs
            if j > n:
               done = True
               j = n
            if first:
               self.sendFrame(opcode = opcode, payload = payload[i:j], fin = done, sync = sync, peer=peer)
               first = False
            else:
               self.sendFrame(opcode = 0, payload = payload[i:j], fin = done, sync = sync, peer=peer)
            i += pfs


   def onMessage(self, msg, binary):
      if len(self.peers)==2:
          if self.peers[0] == self.peerstr:
              self.sendMessage(msg, binary,peer = self.peers[1])
          else:
              self.sendMessage(msg, binary,peer = self.peers[0])



   def connectionMade(self):
      return WebSocketServerProtocol.connectionMade(self)
      
   def onConnect(self,connectionRequest):
      self.peers.append(connectionRequest.peerstr)
      return WebSocketServerProtocol.onConnect(self,connectionRequest)

   def connectionLost(self,reason):
      del self.transports[self.peerstr]
      self.peers.remove(self.peerstr)
      if len(self.peers)==1:
          self.sendMessage('\x03\x52\x65\x6d\x6f\x74\x65\x20\x43\x6c\x69\x65\x6e\x74\x20\x44\x69\x73\x63\x6f\x6e\x6e\x65\x63\x74\x65\x64', binary=True,peer=self.peers[0]) #  /x03 + "Remote Client Disconnected"
      return WebSocketServerProtocol.connectionLost(self,reason)


   
   
if __name__ == '__main__':
      if len(sys.argv) > 1 and sys.argv[1] == 'debug':
         log.startLogging(sys.stdout)
         debug = True
      else:
         debug = False

      factory = WebSocketServerFactory("ws://localhost:9000",
                                       debug = debug,
                                       debugCodePaths = debug)
      factory.protocol = EchoServerProtocol
      factory.setProtocolOptions(allowHixie76 = True)
      listenWS(factory)
      reactor.run()
