"""Fail closed for Python networking. Native-library traffic needs OS audit too."""

import os
import sys


def enforce_offline():
    os.environ.update(
        HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1", HF_HUB_DISABLE_TELEMETRY="1"
    )

    def audit(event, args):
        if event in {
            "socket.__new__",
            "socket.connect",
            "socket.connect_ex",
            "socket.getaddrinfo",
            "socket.gethostbyname",
            "socket.gethostbyaddr",
            "socket.sendto",
            "socket.sendmsg",
            "socket.bind",
        }:
            raise PermissionError("LectureLive runtime networking is disabled")

    sys.addaudithook(audit)
