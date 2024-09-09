import can
import socket
import struct
import threading
import logging

# Configure CAN interface
can_interface = 'can0'
bus = can.interface.Bus(channel=can_interface, bustype='socketcan')

# Configure TCP server
tcp_ip = '0.0.0.0'
tcp_port = 5005
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind((tcp_ip, tcp_port))
server_socket.listen(1)
conn, addr = server_socket.accept()

# Configure logging
logging.basicConfig(filename='server_log.txt', level=logging.INFO, format='%(asctime)s - %(message)s')
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
