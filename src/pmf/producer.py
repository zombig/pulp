#
# Copyright (c) 2010 Red Hat, Inc.
#
# Authors: Jeff Ortel <jortel@redhat.com>
#
# This software is licensed to you under the GNU General Public License,
# version 2 (GPLv2). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv2
# along with this software; if not, see
# http://www.gnu.org/licenses/old-licenses/gpl-2.0.txt.
#
# Red Hat trademarks are not licensed under GPLv2. No permission is
# granted to use or replicate Red Hat trademarks that are incorporated
# in this software or its documentation.
#

"""
Contains AMQP message producer classes.
"""

from pmf import *
from pmf.base import Endpoint
from pmf.dispatcher import Return
from pmf.envelope import Envelope
from qpid.util import connect
from qpid.connection import Connection
from qpid.datatypes import Message
from qpid.queue import Empty


class Producer(Endpoint):
    """
    An AMQP message producer.
    @ivar consumerid: The AMQP consumer (target) queue ID.
    @type consumerid: str
    @ivar sid: The unique AMQP session ID.
    @type sid: str
    @ivar queue: The primary incoming (reply) message queue.
    @type queue: L{qpid.Queue}
    @ivar session: An AMQP session.
    @type session: L{qpid.Session}
    """

    def open(self):
        """
        Open and configure the producer.
          - Open the session.
          - Declare the reply queue.
          - Bind the queue to an exchange.
          - Subscribe to the queue.
        """
        sid = getuuid()
        session = self.connection.session(sid)
        session.queue_declare(queue=sid, exclusive=True)
        session.exchange_bind(
            exchange="amq.direct",
            queue=sid,
            binding_key=sid)
        session.message_subscribe(queue=sid, destination=sid)
        queue = session.incoming(sid)
        queue.start()
        self.sid = sid
        self.consumerid = self.id
        self.session = session
        self.queue = queue

    def send(self, content, synchronous=True):
        """
        Send a message to the consumer.
        @param content: The json encoded payload.
        @type content: str
        @param synchronous: Flag to indicate synchronous.
            When true the I{replyto} is set to our I{sid} and
            to (block) read the reply queue.
        @type synchronous: bool
        """
        sn = getuuid()
        envelope = Envelope(sn=sn, payload=content)
        if synchronous:
            envelope.replyto = ("amq.direct", self.sid)
        dp = self.session.delivery_properties()
        dp.routing_key=self.consumerid
        message = Message(dp, envelope.dump())
        self.session.message_transfer(
            destination='amq.direct',
            message=message)
        if synchronous:
            return self._getreply(sn)
        else:
            return None

    def _getreply(self, sn):
        """
        Read the reply from our reply queue.
        @param sn: The request serial number.
        @type sn: str
        @return: The json unencoded reply.
        @rtype: any
        """
        try:
            message, envelope = self._searchqueue(sn)
            if not message:
                return
            reply = Return()
            reply.load(envelope.payload)
            self.acceptmessage(message.id)
            if reply.succeeded():
                return reply.retval
            else:
                raise Exception, reply.exval
        except Empty:
            # TODO: something better for timeouts.
            pass

    def _searchqueue(self, sn):
        """
        Seach the reply queue for the envelope with
        the matching serial #.
        @param sn: The expected serial number.
        @type sn: str
        @return: (message, envelope)
        @rtype: tuple
        """
        while True:
            result = (None, None)
            message = self.queue.get(timeout=90)
            envelope = Envelope()
            envelope.load(message.body)
            if sn == envelope.sn:
                result = (message, envelope)
                break
            else:
                self.acceptmessage(message.id)
        return result
