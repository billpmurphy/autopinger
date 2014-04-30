import Queue
import multiprocessing
import socket
from math import sqrt
from struct import pack, unpack
from time import time

import ping

class IPRange(object):
    def __init__(self, range_start, range_end):
        self.range_start = ping.ip_to_int(range_start)
        self.range_end = ping.ip_to_int(range_end) + 1
        if self.range_end < self.range_start:
            raise ValueError("Range start must be <= range end")
        self.len_range = self.range_end - self.range_start
        self.generator = self.create_generator()
    def create_generator(self):
        self.generate_prime()
        nb = self.prime % self.len_range
        for i in range(self.len_range):
            yield ping.int_to_ip(nb + self.range_start)
            nb = (nb + self.prime) % self.len_range
    def next(self):
        return self.generator.next()
    def generate_prime(self):
        def is_prime(n):
            for i in range(2, int(sqrt(n) + 1)):
                if n % i == 0:
                    return False
            return True

        next_candidate = self.len_range + int(sqrt(self.len_range))
        while True:
            if is_prime(next_candidate):
                self.prime = next_candidate
                return
            next_candidate += 1


class AutoPinger(object):
    def __init__(self, filename):
        with open(filename, "r") as range_file:
            ranges = [line.strip().split(",") for line in range_file]
        self.ranges = [IPRange(*r) for r in ranges]
    def send_pings(self):
        self.sock = ping.create_raw_socket()
        done = False
        try:
            while not done:
                done = True
                for r in self.ranges:
                    try:
                        addr = r.next()
                        ping.echo(addr, self.sock)
                        done = False
                    except StopIteration:
                        pass
        finally:
            self.sock.close()
        return


class Listener(multiprocessing.Process):
    def __init__(self, filename):
        super(Listener, self).__init__()
        self.filename = filename
        self.sync = multiprocessing.Queue(1)
    def run(self):
        run = True
        try:
            sock = ping.create_raw_socket()
            sock.setblocking(0)
            sock.bind(("", 1))
            with open(self.filename, "a") as writefile:
                while run:
                    try:
                        response, addr = sock.recvfrom(1024)
                        writefile.write("%s,%s\n" % (addr[0], int(time())))
                    except socket.error:
                        pass
                    except Exception as e:
                        print e

                    try:
                        run = bool(self.sync.get_nowait())
                    except Queue.Empty:
                        pass
                    except:
                        run = False
        finally:
            sock.close()
    def stop(self):
        self.sync.put(False)
        return
