#!/usr/bin/env python3
from pymongo import MongoClient
from collections import defaultdict
import time
import os

class UserMails:
    def __init__(self,logger):
        self.logger = logger
        self.mdbe = MongoClient( os.getenv( "MONGODB_URI","mongodb://localhost/" ), connect = False )
        self.mdb = self.mdbe[ os.getenv("MONGODB_DB")]

    def query(self):
        for user in self.mdb["users"].find({"mails.0":{"$exists":True}}):
            for mail in user["mails"]:
                tpl,_,params = mail.partition(":")
                params = params.split(":")
                yield {
                    "type":"Mail",
                    "user":user,
                    "mail":mail,
                    "tpl":["user_%s.%s" % (tpl,user["lang"]),"user_%s" % tpl],
                    "params":params,
                    "receivers":[user["email"]],
                }

    def ack_sent(self,msg):
        self.mdb["users"].update_one({"_id":msg["user"]["_id"]},{"$pull":{"mails":msg["mail"]}})
