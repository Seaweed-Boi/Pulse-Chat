#!/usr/bin/env python3
"""Small load-test utility for Pulse-Chat."""

import argparse
import os
import socket
import ssl
import sys
import threading
import time
from typing import Dict, List, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.message_protocol import MessageProtocol


class LoadTestClient:
    def __init__(self, host: str, port: int, username: str, password: str):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.socket = None
        self.file = None
        self.auth_ok = threading.Event()
        self.failed = False
        self.failure_reason = ""
        self.received_times: Dict[str, float] = {}
        self.lock = threading.Lock()
        self.receiver = None

    def connect(self, timeout: float) -> bool:
        try:
            raw_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            raw_socket.settimeout(timeout)
            context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            secure_socket = context.wrap_socket(
                raw_socket,
                server_hostname=self.host,
            )
            secure_socket.connect((self.host, self.port))
            secure_socket.settimeout(None)
            self.socket = secure_socket
            self.file = secure_socket.makefile("rb")
            self.receiver = threading.Thread(target=self._receive_loop, daemon=True)
            self.receiver.start()

            auth_message = MessageProtocol.create_message(
                MessageProtocol.TYPE_AUTH,
                self.username,
                "authenticate",
                password=self.password,
            )
            self.socket.sendall(MessageProtocol.encode_message(auth_message))
            return self.auth_ok.wait(timeout)
        except Exception as exc:
            self.failed = True
            self.failure_reason = str(exc)
            return False

    def send_chat(self, content: str, room: str = "lobby"):
        if not self.socket:
            raise RuntimeError("Client not connected")
        message = MessageProtocol.create_message(
            MessageProtocol.TYPE_CHAT,
            self.username,
            content,
            room=room,
        )
        self.socket.sendall(MessageProtocol.encode_message(message))

    def _receive_loop(self):
        try:
            while True:
                line = self.file.readline()
                if not line:
                    return
                message = MessageProtocol.decode_message(line)
                if not message:
                    continue
                msg_type = message.get("type")
                if msg_type == MessageProtocol.TYPE_AUTH_OK:
                    self.auth_ok.set()
                elif msg_type == MessageProtocol.TYPE_ERROR:
                    self.failed = True
                    self.failure_reason = message.get("content", "Unknown error")
                elif msg_type == MessageProtocol.TYPE_CHAT:
                    content = message.get("content", "")
                    with self.lock:
                        self.received_times[content] = time.perf_counter()
        except Exception as exc:
            if not self.failed:
                self.failed = True
                self.failure_reason = str(exc)

    def wait_for_message(self, content: str, timeout: float) -> Optional[float]:
        deadline = time.perf_counter() + timeout
        while time.perf_counter() < deadline:
            with self.lock:
                if content in self.received_times:
                    return self.received_times[content]
            time.sleep(0.01)
        return None

    def close(self):
        try:
            if self.socket:
                leave_message = MessageProtocol.create_message(
                    MessageProtocol.TYPE_LEAVE,
                    self.username,
                    "disconnect",
                )
                self.socket.sendall(MessageProtocol.encode_message(leave_message))
        except Exception:
            pass
        try:
            if self.file:
                self.file.close()
        except Exception:
            pass
        try:
            if self.socket:
                self.socket.close()
        except Exception:
            pass


def parse_args():
    parser = argparse.ArgumentParser(description="Pulse-Chat client load test")
    parser.add_argument("--host", default="localhost")
    parser.add_argument("--port", type=int, default=5555)
    parser.add_argument("--clients", type=int, default=10)
    parser.add_argument("--password", default="demo-pass")
    parser.add_argument("--timeout", type=float, default=10.0)
    return parser.parse_args()


def main():
    args = parse_args()
    clients: List[LoadTestClient] = []

    connect_start = time.perf_counter()
    success_count = 0
    failure_reasons: List[str] = []

    try:
        for index in range(args.clients):
            client = LoadTestClient(
                host=args.host,
                port=args.port,
                username=f"load_user_{index}",
                password=args.password,
            )
            clients.append(client)
            if client.connect(args.timeout):
                success_count += 1
            else:
                failure_reasons.append(
                    f"{client.username}: {client.failure_reason or 'auth timeout'}"
                )

        connect_duration = time.perf_counter() - connect_start
        print(f"Requested clients: {args.clients}")
        print(f"Connected clients: {success_count}")
        print(f"Connection phase time: {connect_duration:.3f}s")

        if success_count == 0:
            print("No clients connected successfully.")
            if failure_reasons:
                print("Failures:")
                for reason in failure_reasons:
                    print(f"  - {reason}")
            return

        sender = clients[0]
        message_text = f"LOAD_TEST_MESSAGE_{int(time.time())}"
        send_started = time.perf_counter()
        sender.send_chat(message_text)

        delivery_latencies: List[float] = []
        delivered_count = 0
        for client in clients[:success_count]:
            delivered_at = client.wait_for_message(message_text, args.timeout)
            if delivered_at is None:
                continue
            delivered_count += 1
            delivery_latencies.append(delivered_at - send_started)

        print(f"Broadcast recipients reached: {delivered_count}/{success_count}")
        if delivery_latencies:
            print(f"Broadcast latency min: {min(delivery_latencies) * 1000:.2f} ms")
            print(f"Broadcast latency avg: {(sum(delivery_latencies) / len(delivery_latencies)) * 1000:.2f} ms")
            print(f"Broadcast latency max: {max(delivery_latencies) * 1000:.2f} ms")

        if failure_reasons:
            print("Failures:")
            for reason in failure_reasons:
                print(f"  - {reason}")
    finally:
        for client in clients:
            client.close()


if __name__ == "__main__":
    main()
