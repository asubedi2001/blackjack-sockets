# Blackjack

This project is a blackjack card game implementation using sockets.

# Usage

In two seperate terminals, run each of the following: \
```python server.py {port number}``` \
```python client.py {address} {port number}```

# Notes

server.py uses 127.0.0.1 as the default address. If warranted, this may be changed, functionality will not change.

Input validation is performed client side as the user is assumed to be trustworthy, however this functionality can be moved over to the server side with little change if this is not the case.