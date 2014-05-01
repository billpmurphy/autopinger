import heapq
import Queue
import multiprocessing
import socket
from math import sqrt
from struct import pack, unpack
from sys import stderr
from time import time

import ping

class IPRange(object):
    """
    A generator containing a range of IPv4 addresses that can be iterated over
    in psuedorandom order.
    """
    def __init__(self, range_start, range_end):
        self.range_start = ping.ip_to_int(range_start)
        self.range_end = ping.ip_to_int(range_end) + 1
        if self.range_end < self.range_start:
            raise ValueError("Range start must be <= range end")
        self.len_range = self.range_end - self.range_start
        self._generator = self._start_full_cycle()
    def __iter__(self):
        return self._generator
    def __len__(self):
        return self.len_range
    def next(self):
        """
        Return the next IP address in the psuedorandom sequence.
        """
        return self._generator.next()
    def visited(self):
        return self._visited
    def _start_full_cycle(self):
        """
        Begin the full cycle algorithm on the IP range, returning a generator.
        """
        self._generate_prime()
        self._visited = 0
        nb = self._prime % self.len_range
        for i in range(self.len_range):
            yield ping.int_to_ip(nb + self.range_start)
            self._visited += 1
            nb = (nb + self._prime) % self.len_range
    def _generate_prime(self):
        """
        Generate a new prime number larger than the range of addresses for the
        purpose of running the full cycle algorithm to psuedorandomly iterate
        over the range.
        """
        def is_prime(n):
            for i in range(2, int(sqrt(n) + 1)):
                if n % i == 0:
                    return False
            return True
        next_candidate = self.len_range + int(sqrt(self.len_range))
        while True:
            if is_prime(next_candidate):
                self._prime = next_candidate
                return
            next_candidate += 1


class AutoPinger(object):
    """
    An object containing a list of IP ranges and a socket with which to send
    ICMP requests to them in psuedorandom order.
    """
    def __init__(self, filename):
        with open(filename, "r") as range_file:
            ranges = [line.strip().split(",") for line in range_file]
        self.ranges = [IPRange(*r) for r in ranges]
    def send_pings(self):
        """
        Create a socket and send pings to every address in the list of ranges.
        """
        sock = ping.create_raw_socket()
        range_heap = []
        for add_range in self.ranges:
            heapq.heappush(range_heap, (0, add_range))

        try:
            while range_heap:
                try:
                    add_range = heapq.heappop(range_heap)[1]
                    ping.echo(add_range.next(), sock)
                    heapq.heappush(
                        range_heap,
                        (add_range.visited()/float(len(add_range)), add_range)
                    )
                except StopIteration:
                   continue
        finally:
            sock.close()
        return


class Listener(multiprocessing.Process):
    """
    A subprocess that listens for incoming ICMP responses and writes them to a
    text file.
    """
    def __init__(self, filename):
        super(Listener, self).__init__()
        self.filename = filename
        self.sync = multiprocessing.Queue(1)
    def run(self):
        """
        Start listening for incoming packets. If a malformed packet is
        encountered, write to stderr but continue listening for more packets.
        If self.stop() is called, cease listening and terminate the Listener
        subprocess.
        """
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
                        stderr.write(e)

                    try:
                        run = bool(self.sync.get_nowait())
                    except Queue.Empty:
                        continue
                    except Exception as e:
                        stderr.write(e)
                        run = False
        finally:
            sock.close()
    def stop(self):
        """
        Stop the Listener.
        """
        if self.is_alive():
            self.sync.put(False)
        return
