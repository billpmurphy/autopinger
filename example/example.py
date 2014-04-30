from time import sleep

import autopinger

def main(filename):
    # start the listener
    listener = autopinger.Listener("test.txt")
    listener.start()

    # send pings
    pinger = autopinger.AutoPinger(filename)
    pinger.send_pings()

    # wait for replies and then stop the listener
    sleep(10)
    listener.stop()

if __name__ == "__main__":
    main("example.txt")
