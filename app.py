from tornado import ioloop, httpserver
from tornado.options import parse_command_line
import ssl

# User modules
from game import *   # classes: user, db
from comm import *   # classes: cls
from stats import PStat
# from httpHandler import *

# classes start with P are page classes and start with C are general classes.
# cid: User crediential
# sid: secured rid.
# rid: room id.
# uid: username.


class PMain(BaseCls):
    def get(self, *args, **kwargs):
        rlog.i('Main page request. from {0}'.format(self.request.remote_ip))
        self.write("<a href='/login'> User Login </a><br>")
        self.write("<a href='/reg'> User Signup </a><br>")
        self.write("<a href='/game'> Game Lobby </a><br>")
        self.write("<a href='/stats'> Game Statistical Data </a>")


app = web.Application(
    [
        (web.HostMatches(r'(localhost|127\.0\.0\.1|192\.168\.1\.151|192\.168\.233\.110)'),  # Against DNS rebinding.
         [
             (r"/", PMain),
             (r"/login", PLogin),
             (r"/reg", PSignUp),
             (r"/auth", PAuth),
             (r"/game", PGame),
             (r"/room", PRoom),
             (r"/data", PData),
             (r"/stats", PStat),
         ]),
    ],
    **settings
)

if __name__ == '__main__':

    parse_command_line()

    # set logger for debugging.
    if settings['debug']:
        d_logger = CStreamLog()

    # Configuring area BEGIN.
    port = 23333
    ws_port = ws_settings['port']
    SSLOpt = {
        "ssl_version": ssl.PROTOCOL_TLSv1_2,
        # 127.0.0.1 certificate and pk
        "certfile": os.path.abspath(".") + "/https/server.x509.crt",
        "keyfile": os.path.abspath(".") + "/https/server.rsa2.key",
        # LAN ip certificate and pk
        # "certfile": os.path.abspath(".") + "/https/server110.crt",
        # "keyfile": os.path.abspath(".") + "/https/server110.key"
    }
    # Configuring area END.

    print("Game server is initating....")

    app.listen(ws_port, ssl_options=SSLOpt)
    print("Listening WSS port {port}".format(port=ws_port))

    hs = httpserver.HTTPServer(app, ssl_options=SSLOpt)
    hs.listen(port)
    print("Listening HTTPS port {port}".format(port=port))
    ioloop.IOLoop.instance().start()
