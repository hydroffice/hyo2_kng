import logging

logger = logging.getLogger(__name__)


class Sis4Msg:

    sis4_msg_types = {
        r"N/A": 0,
        r"TX SVP": 1,
        r"REQUEST CURRENT SVP": 2
    }

    def __init__(self, msg_type: str):

        if msg_type not in self.sis4_msg_types.keys():
            raise RuntimeError("invalid message type: %s" % msg_type)

        self.type = msg_type
        self.msg = str()
        self.is_ready = False

    def make_tx_svp(self):
        if self.type != r"TX SVP":
            raise RuntimeError("invalid message type: %s" % self.type)

        self.is_ready = True

    def make_request_current_svp(self):
        if self.type != r"REQUEST CURRENT SVP":
            raise RuntimeError("invalid message type: %s" % self.type)

        self.is_ready = True
