# -*- coding: utf-8 -*-
import sys
import weakref

import tornado.ioloop
import tornado.web

import sockjs.tornado

from sockjs.tornado import SockJSRouter, SockJSConnection

import tornadoredis
import tornadoredis.pubsub


class IndexHandler(tornado.web.RequestHandler):
    """Regular HTTP handler to serve the chatroom page"""

    def get(self):
        self.render('index.html')


subscriber = tornadoredis.pubsub.SockJSSubscriber(tornadoredis.Client())


class MessageConnection(SockJSConnection):
    """Echo connection implementation"""
    clients = {}

    def on_open(self, info):
        # When new client comes in, will add it to the clients list
        key = info.cookies['csrftoken'].value
        print(key)
        self.clients[key] = self
        self.user_id = key
        subscriber.subscribe(
            ['broadcast_channel', 'private.{}'.format(self.user_id)], self)

    def on_message(self, msg):
        # For every incoming message, broadcast it to all clients
        print(msg)

    def on_close(self):
        # If client disconnects, remove him from the clients list
        print(self)
        subscriber.unsubscribe('private.{}'.format(self.user_id), self)

    @classmethod
    def pubsub(cls, data):
        key, message = data
        print(key, message)

        client = cls.clients.get(key)
        if client:
            client.send(message)


if __name__ == '__main__':
    # 1. Create SockJSRouter
    ChatRouter = SockJSRouter(MessageConnection, '/chat')

    # 2. Create Tornado web.Application

    app = tornado.web.Application(
        [(r"/", IndexHandler)] + ChatRouter.urls
    )

    # 3. Make application listen on port 8080
    app.listen(8080)
    print('http://127.0.0.1:8080/')
    # 5. Start IOLoop
    tornado.ioloop.IOLoop.instance().start()
