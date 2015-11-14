import json
import logging
import queue
import sys
from logging.handlers import QueueListener, QueueHandler
from os import mkdir
from os.path import join, dirname, exists
from psycopg2.pool import ThreadedConnectionPool
from concurrent.futures import ThreadPoolExecutor
from random import randrange
from tornado.ioloop import IOLoop
from tornado.web import Application, RequestHandler, asynchronous, stream_request_body
from tornado.websocket import WebSocketHandler
from tornado.httpclient import HTTPRequest, AsyncHTTPClient
from tornado.log import enable_pretty_logging
from tornado.process import cpu_count
from create_db import dsn

q = queue.Queue(-1)
formatter = logging.Formatter(style='{', datefmt='%H:%M:%S', fmt='[{levelname} {name} {asctime}] {message}')
stream_hndl = logging.StreamHandler(stream=sys.stderr)
stream_hndl.setFormatter(formatter)
stream_hndl.setLevel(logging.DEBUG)
listener = QueueListener(q, stream_hndl)

queued_hndl = QueueHandler(q)
queued_hndl.setLevel(logging.DEBUG)
logger = logging.getLogger()
logger.addHandler(queued_hndl)
logger.setLevel(logging.DEBUG)
listener.start()

ConnPool = ThreadedConnectionPool(1, cpu_count()*2, dsn)
WorkresPool = ThreadPoolExecutor(cpu_count())
Clients = {}
UPLOAD_DIR = 'upload'


class MainWebSocketHandler(WebSocketHandler):

    def check_origin(self, origin):
        return True

    def on_message(self, message):
        logger.info(message)
        self.client_id = json.loads(message).get('client_id')
        logger.debug(self.client_id) #todo не рыботает вывод уровня DEBUG
        if self.client_id:
            Clients[self.client_id] = self
        logger.debug(Clients)

    def open(self):
        logger.info("WebSocket opened")

    def on_close(self):
        del Clients[self.client_id]
        logger.info("WebSocket closed")


class MainHandler(RequestHandler):

    def get(self, *args, **kwargs):
        self.set_cookie('client_id', '777')
        self.render('static/main.html')


class DownloadHandler(RequestHandler):

    def _chunk_downloading_callback(self, data):

        self.file.write(data)
        self.file.flush()

    def _done_downloading_callback(self, response):
        self.file.close()
        self.write('DOWNLOADED')
        self.finish()

    @asynchronous
    def get(self, *args, **kwargs):
        logger.info('start download')
        filename = 'file-{}'.format(id(self.request.connection))
        self.file = open(filename, 'wb')

        req = HTTPRequest('http://fourthirds-user.com/images/204/E-P1-fromRAW-sRGB.jpg',
                          streaming_callback=self._chunk_downloading_callback)

        async_client = AsyncHTTPClient()
        async_client.fetch(req, self._done_downloading_callback)


@stream_request_body
class UploadHandler(RequestHandler): #todo раделять файлы multipart/form-data

    def prepare(self):
        client_id = int(self.get_cookie('client_id'))
        self.ws = Clients[client_id]
        self.received = 0

        if not exists(UPLOAD_DIR):
            mkdir(UPLOAD_DIR)

        self.file = open(join(UPLOAD_DIR,'uploaded_file'), 'wb')

    def data_received(self, chunk):
        length = len(chunk)
        self.received += length
        logger.info('Chunk length: {}'.format(length))

        self.ws.write_message({'received': self.received})
        self.file.write(chunk)

    def post(self, *args, **kwargs):
        self.file.close()
        self.write('UPLOADED')


class DbHandler(RequestHandler):

    def _query(self):
        logger.info('used pg connections: %s , max connections: %s ' % (len(ConnPool._used), ConnPool.maxconn))
        conn = ConnPool.getconn()
        cur = conn.cur()

        sec = randrange(1, 4)
        cur.execute("""SELECT pg_sleep(3);""")
        cur.close()

        ConnPool.putconn(conn)

    def _query_done(self, future):
        self.write('QUERIED')
        self.finish()

    @asynchronous
    def get(self, *args, **kwargs):
        logger.info('start query')
        logger.info('threads count: %s' % len(WorkresPool._threads))

        future = WorkresPool.submit(self._query)
        future.add_done_callback(self._query_done)


app = Application([(r'/websocket', MainWebSocketHandler),

                   (r'/', MainHandler),
                   (r'/upload', UploadHandler),
                   (r'/download', DownloadHandler),
                   (r'/db', DbHandler)
                   ],

                  # debug=True,
                  static_path=join(dirname(__file__), 'static'),
                  cookie_secret='SECRET_KEY',
                  compiled_template_cache=False,
                  static_hash_cache=False)


if __name__ == '__main__':
    enable_pretty_logging()
    app.listen(7777, max_body_size=150*1024*1024)
    IOLoop.current().start()
