import can
import socket
import struct
import threading
import logging
import time

# Configure CAN interface
can_interface = 'can0'
bus = can.interface.Bus(channel=can_interface, bustype='socketcan')

# Configure TCP server
tcp_ip = '0.0.0.0'
tcp_port = 5005
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind((tcp_ip, tcp_port))
server_socket.listen(1)

# Configure TCP client
client_tcp_ip = '192.168.100.175'  # IP address of the server (Raspberry Pi 1)
client_tcp_port = 5005
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger()

def server_thread():
    conn, addr = server_socket.accept()
    logging.info(f"Connection from: {addr}")

    def send_can_to_tcp():
        while True:
            msg = bus.recv(timeout=1.0)
            if msg:
                data = struct.pack('I8s', msg.arbitration_id, msg.data)
                conn.send(data)
                logging.info(f"Sent CAN message: {msg}")

    def recv_tcp_to_can():
        while True:
            data = conn.recv(12)
            if data:
                arbitration_id, msg_data = struct.unpack('I8s', data)
                msg = can.Message(arbitration_id=arbitration_id, data=msg_data, is_extended_id=False)
                bus.send(msg)
                logging.info(f"Received TCP message: {msg}")

    try:
        send_thread = threading.Thread(target=send_can_to_tcp)
        recv_thread = threading.Thread(target=recv_tcp_to_can)
        send_thread.start()
        recv_thread.start()
        send_thread.join()
        recv_thread.join()

    except KeyboardInterrupt:
        logging.info("Server interrupted by user")

    finally:
        conn.close()
        server_socket.close()
        logging.info("Server connection closed")

def client_thread():
    while True:
        try:
            client_socket.connect((client_tcp_ip, client_tcp_port))
            logging.info(f"Connected to server at: {client_tcp_ip}:{client_tcp_port}")
            break
        except ConnectionRefusedError:
            logging.info("Connection refused, retrying in 5 seconds...")
            time.sleep(5)

    def send_can_to_tcp():
        while True:
            try:
                msg = bus.recv(timeout=1.0)
                if msg:
                    data = struct.pack('I8s', msg.arbitration_id, msg.data)
                    client_socket.send(data)
                    logging.info(f"Sent CAN message: {msg}")
            except (BrokenPipeError, ConnectionResetError):
                logging.info("Connection lost, attempting to reconnect...")
                client_socket.close()
                client_thread()
                break

    def recv_tcp_to_can():
        while True:
            try:
                data = client_socket.recv(12)
                if data:
                    arbitration_id, msg_data = struct.unpack('I8s', data)
                    msg = can.Message(arbitration_id=arbitration_id, data=msg_data, is_extended_id=False)
                    bus.send(msg)
                    logging.info(f"Received TCP message: {msg}")
            except (BrokenPipeError, ConnectionResetError):
                logging.info("Connection lost, attempting to reconnect...")
                client_socket.close()
                client_thread()
                break

    try:
        send_thread = threading.Thread(target=send_can_to_tcp)
        recv_thread = threading.Thread(target=recv_tcp_to_can)
        send_thread.start()
        recv_thread.start()
        send_thread.join()
        recv_thread.join()

    except KeyboardInterrupt:
        logging.info("Client interrupted by user")

    finally:
        client_socket.close()
        logging.info("Client connection closed")

# Start server and client threads
server = threading.Thread(target=server_thread)
client = threading.Thread(target=client_thread)

server.start()
client.start()

server.join()
client.join()
