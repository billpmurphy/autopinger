Survey the IPv4 address space
=============================

Pure-Python tool that pings every IPv4 address in a user-defined set of ranges
(up to and including every IPv4 address ever) and records the addresses of
peers that responded. Useful if you want to survey sections of IPv4 for
whatever reason.

To install:

```
git clone https://github.com/billpmurphy/autopinger.git autopinger
cd autopinger
python setup.py install
```

To run the example (pings some of Google's servers and saves the responses to
a text file):

```
sudo python example/example.py
```
