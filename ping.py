import socket
from time import time
from random import random
from struct import pack, unpack

ICMP_ECHO_REQUEST = 8
ERROR_DESCR = {
    1: "ICMP messages can only be sent from processes running as root.",
    10013: "ICMP messages can only be sent by users or processes with administrator rights."
}


def checksum(source):
    """
    Standard IP checksum algorithm.
    """
    checksum = 0
    count_to = len(source) & -2
    count = 0

    while count < count_to:
        this_val = ord(source[count + 1]) * 256 + ord(source[count])
        checksum += this_val
        checksum &= 0xffffffff
        count += 2

    if count_to < len(source):
        checksum += ord(source[len(source) - 1])
        checksum &= 0xffffffff

    checksum = (checksum >> 16) + (checksum & 0xffff)
    checksum += checksum >> 16
    answer = ~checksum
    answer &= 0xffff
    return answer >> 8 | (answer << 8 & 0xff00)


def create_packet(id):
    """
    Creates a new echo request packet based on the given "id".
    """
    # Builds dummy header
    # Header: type (8), code (8), checksum (16), id (16), sequence (16)
    header = pack("bbHHh", ICMP_ECHO_REQUEST, 0, 0, id, 1)
    data = 192 * "Q"

    # Builds real header
    header = pack("bbHHh", ICMP_ECHO_REQUEST, 0,
            socket.htons(checksum(header + data)), id, 1)
    return header + data


def create_raw_socket():
    """
    Create a new raw socket for sending/receiving ICMP messages.
    """
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_RAW,
                socket.IPPROTO_ICMP)
    except socket.error as err:
        err_num, err_msg = err.args
        if err_num in ERROR_DESCR:
            raise socket.error(ERROR_DESCR[err_num])  # operation not permitted
        else:
            raise socket.error(err_msg)
    return sock


def echo(dest_addr, ping_sock=None):
    """
    Sends one ICMP echo request to a given host.
    """
    if ping_sock is None:
        sock = create_raw_socket()
    else:
        sock = ping_sock

    packet_id = int(random() % 65535)
    packet = create_packet(packet_id)
    while packet:
        # The ICMP protocol does not use a port, but the function
        # below expects it, so we just give it a dummy port.
        sent = sock.sendto(packet, (dest_addr, 1))
        packet = packet[sent:]

    if ping_sock is None:
        # If we created this socket on the fly for this echo, close it
        sock.close()
    return


def listen(callback):
    """
    Listen for incoming ICMP packets on any port, and execute a callback
    function on each ICMP packet when it is received.
    """
    sock = create_raw_socket()
    sock.bind(("", 1))
    try:
        while True:
            callback(sock.recv(1024))
    except KeyboardInterrupt:
        print("Done.")
    finally:
        sock.close()
    return

