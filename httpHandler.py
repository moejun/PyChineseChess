import tornado.web
import tornado.ioloop
from app import port


class HttpRedirector(tornado.web.RequestHandler):

    def prepare(self):
        if self.request.protocol == 'http':
            print(port)
            self.redirect('https://' + self.request.host + port, permanent=False)

    def get(self):
        pass




