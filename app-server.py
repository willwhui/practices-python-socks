import socket
import selectors
import types

def accept_wrapper(sock):
    # accept and get a connection (of a client)
    conn, addr = sock.accept()
    print('accepted connection from', addr)
    conn.setblocking(False)
    # Only when the 'outb' is attached to 
    # the 'conn' object, we can get the data send by  
    # the client. Because the client may send it's data 
    # to the sever by several times calling of send()
    data = types.SimpleNamespace(addr=addr, inb=b'', outb=b'')
    events = selectors.EVENT_READ | selectors.EVENT_WRITE
    # register the 'conn' object to make it monitored by
    # the selector
    sel.register(conn, events, data=data)


def service_connection(key, mask):
    # we got a readied connection
    sock = key.fileobj
    data = key.data
    if mask & selectors.EVENT_READ:
        recv_data = sock.recv(1024)  # Should be ready to read
        if recv_data:
            data.outb += recv_data
        else: # all data recieved
            print('closing connection to', data.addr)
            sel.unregister(sock)
            # sock.close() just means stop using it
            # the real will disconnected when both server
            #  and client call sock.close()
            # But, will the sock.send() below fail in some
            #  cases? 
            sock.close()
    # When the socket is ready for writing, which should 
    # always be the case for a healthy socket, any received
    # data stored in data.outb is echoed to the client using 
    # sock.send(). 
    # The bytes sent are then removed from the send buffer
    # Obove text is from the tutourial, that means the 
    # recieved data will be send to the client imediately.
    if mask & selectors.EVENT_WRITE:
        if data.outb:
            print('echoing', repr(data.outb), 'to', data.addr)
            sent = sock.send(data.outb)  # Should be ready to write
            data.outb = data.outb[sent:]


host = '127.0.0.1'  # Standard loopback interface address (localhost)
port = 65432        # Port to listen on (non-privileged ports are > 1023)

# better try to understand the OS system select() API
# and the Python selector class first.
sel = selectors.DefaultSelector()

lsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
lsock.bind((host, port))
lsock.listen()
print('listening on', (host, port))
lsock.setblocking(False)

# 1. more than one file object can be registered into the 
# selector 
# 2. the 'None' value data will be stored in the sel.select() 
# returned events item, and will be used as the flag of
# the 'lsock' object
sel.register(lsock, selectors.EVENT_READ, data=None)
while True:
    # the select method always return a list of readied objects
    events = sel.select(timeout=None)
    for key, mask in events:
        if key.data is None: # the 'None' value as a flag
            # the 'lsock' object is ready to accepting a client
            # when a client is connecting
            accept_wrapper(key.fileobj)
        else:
            # a connected (accepted) client is ready to read
            # or write
            service_connection(key, mask)