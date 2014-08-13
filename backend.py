__author__ = 'Serebatos'
import SocketServer


class Core(object):
    statDict = dict()
    ON = 1
    OFF = 0

    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super(Core, cls).__new__(cls)
        return cls.instance


    def set_on(self, key):
        self.set_val(key, Core.ON)

    def set_off(self, key):
        self.set_val(key, Core.OFF)

    def invert(self,key):
        if key in self.statDict and self.statDict[key] == 0:
            self.set_on(key)
            print "Turning On"
        else:
            self.set_off(key)
            print "Turning Off"

    def set_val(self, key, val):
        self.statDict[key] = val

    def get_status(self):
        return self.statDict

    def get_or_add_action(self, action):
        if action in self.statDict:
            return {action:self.statDict[action]}
        else:
            self.statDict[action]=0
            return {action:self.statDict[action]}

class MyTCPHandler(SocketServer.BaseRequestHandler):
    c = Core()
    """
    The RequestHandler class for our server.

    It is instantiated once per connection to the server, and must
    override the handle() method to implement communication to the
    client.
    """

    def __init__(self, request, client_address, server):
        print "On Enter current status={}".format(c.get_status())
        SocketServer.BaseRequestHandler.__init__(self, request, client_address, server)



    def handle(self):
        # self.request is the TCP socket connected to the client
        self.data = self.request.recv(1024).strip()
        print "{} wrote:".format(self.client_address[0])
        print self.data
        action = c.get_or_add_action(self.data)

        c.invert(self.data)
        print "On Exit current status={}".format(c.get_status())
        # just send back the same data, but upper-cased
        self.request.sendall(self.data.upper())


if __name__ == "__main__":
    HOST, PORT = "localhost", 9999
    c = Core()
    print "n={}".format(c.get_status())
    # Create the server, binding to localhost on port 9999
    server = SocketServer.TCPServer((HOST, PORT), MyTCPHandler)

    # Activate the server; this will keep running until you
    # interrupt the program with Ctrl-C
    server.serve_forever()


    # class MyTCPHandler(SocketServer.StreamRequestHandler):
    #     count = 0
    #
    #     def __init__(self, request, client_address, server):
    #         MyTCPHandler.count = MyTCPHandler.count+1
    #         print "n={}".format(MyTCPHandler.count)
    #         SocketServer.BaseRequestHandler.__init__(self, request, client_address, server)
    #
    #
    #     def handle(self):
    #         # self.rfile is a file-like object created by the handler;
    #         # we can now use e.g. readline() instead of raw recv() calls
    #
    #         self.data = self.rfile.readline().strip()
    #         print "{} wrote!:".format(self.client_address[0])
    #         print self.data
    #         # Likewise, self.wfile is a file-like object used to write back
    #         # to the client
    #         self.wfile.write(self.data.upper())