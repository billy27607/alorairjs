import can
import socket
import struct
import threading
import logging

# Configure CAN interface
can_interface = 'can0'
bus = can.interface.Bus(channel=can_interface, bustype='socketcan')

# Configure TCP client
tcp_ip = '192.168.101.16'  # IP address of the server (Raspberry Pi 1)
tcp_port = 5005
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect((tcp_ip, tcp_port))

# Configure logging
logging.basicConfig(filename='client_log.txt', level=logging.INFO, format='%(asctime)s - %(message)s')
logging.info(f"Connected to server at: {tcp_ip}:{tcp_port}")

def send_can_to_tcp():
    while True:
        msg = bus.recv(timeout=1.0)
        if msg:
            data = struct.pack('I8s', msg.arbitration_id, msg.data)
            client_socket.send(data)
            logging.info(f"Sent CAN message: {msg}")

def recv_tcp_to_can():
    while True:
        data = client_socket.recv(12)
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
    logging.info("Client interrupted by user")

finally:
    client_socket.close()
    logging.info("Client connection closed")
