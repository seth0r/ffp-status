#!/usr/bin/env python3
from sqlalchemy import select,String
import tsdb

class UserMails:
    def __init__(self,logger):
        self.logger = logger

    def query(self):
        with tsdb.getSess() as sess:
            for user in sess.execute( select(tsdb.User)
                .where(tsdb.User.active == True)
                .where(tsdb.User.mails.cast(String) != "[]")
            ).scalars():
                for mail in user.mails:
                    tpl,_,params = mail.partition(":")
                    params = params.split(":")
                    yield {
                        "type":"Mail",
                        "user":user,
                        "mail":mail,
                        "tpl":["user_%s.%s" % (tpl,user.settings["lang"]),"user_%s" % tpl],
                        "params":params,
                        "receivers":[user.email],
                    }

    def ack_sent(self,msg):
        with tsdb.getSess() as sess:
            sess.begin()
            user = sess.get(tsdb.User, {"userid":msg["user"].userid})
            user.mails.remove(msg["mail"])
            sess.commit()
