from time import sleep

import autopinger

def main(data_filename, log_filename):
    # start the listener
    listener = autopinger.Listener(log_filename)
    listener.start()

    # load ranges from file
    with open(data_filename, "r") as range_file:
        ranges = [line.strip().split(",") for line in range_file]

    # send pings
    pinger = autopinger.AutoPinger(ranges)
    pinger.send_pings()

    # wait for replies and then stop the listener
    sleep(10)
    listener.stop()

if __name__ == "__main__":
    main("example.txt", "example_log.txt")
