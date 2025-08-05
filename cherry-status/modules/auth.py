import cherrypy
from cherrypy._cperror import HTTPRedirect
import os
import time
import datetime as dt
import math
import secrets
import inspect
import json
from sqlalchemy import select,delete
from sqlalchemy.sql.expression import func
import tsdb
from argon2 import PasswordHasher
from argon2.exceptions import VerificationError

def valid_domain( s ):
    dot = s.find(".")
    if dot < 1 or dot > len(s) - 3:
        return False
    for c in s:
        if c.isascii() and c.isalnum():
            continue
        if c in "-.":
            continue
        return False
    return True

def valid_username( s ):
    if len(s) == 0:
        return False
    if s.isascii() and s.isalnum():
        return True
    for c in s:
        if c.isascii() and c.isalnum():
            continue
        if c in "+-_.":
            continue
        return False
    return True

def valid_email( s ):
    acc,_,domain = s.partition("@")
    return valid_username(acc) and valid_domain(domain)

class Auth:
    def _check_password(self,pwhash,password):
        try:
            ph = PasswordHasher()
            if ph.verify(pwhash, password):
                return True
        except VerificationError:
            pass
        return False

    def _login(self,username,password):
        with tsdb.getSess() as sess:
            user = sess.execute( select(tsdb.User)
                .where(tsdb.User.username == username)
                .where(tsdb.User.active == True)
            ).scalar_one_or_none()
            if user and user.pwhash:
                if self._check_password(user.pwhash, bytes(password,"utf-8")):
                    sessid = secrets.token_hex()
                    ph = PasswordHasher()
                    if ph.check_needs_rehash(user.pwhash):
                        user.pwhash = ph.hash(bytes(password,"utf-8"))
                    expire = dt.datetime.now(dt.timezone.utc) + dt.timedelta(days=1)
                    user.sessions.append(tsdb.Session( sessid = sessid, expire = expire ))
                    sess.commit()
                    cookie = cherrypy.response.cookie
                    cookie['sessid'] = sessid
                    cookie['sessid']['path'] = '/'
                    cookie['sessid']['max-age'] = 24*60*60
                    cookie['sessid']['version'] = 1
                    return True
        return False

    def _register(self,username,email,email_again, **kwargs):
        with tsdb.getSess() as sess:
            if len(username) < 3:
                return "username_to_short"
            if not valid_username(username):
                return "username_invalid"
            if email != email_again:
                return "email_nomatch"
            if not valid_email(email):
                return "email_invalid"
            if sess.execute( select(tsdb.User).with_only_columns(func.count()).where(tsdb.User.username == username) ).scalar() > 0:
                return "exists"
            if sess.execute( select(tsdb.User).with_only_columns(func.count()).where(tsdb.User.email == email) ).scalar() > 0:
                return "exists"
            user = tsdb.User( username = username, email = email )
            sess.add(user)
            user.pwtoken = secrets.token_urlsafe(256)
            user.pwtokenexpire = dt.datetime.now(dt.timezone.utc) + dt.timedelta(days = 1)
            user.mails = ["pwinit"]
            user.settings = {}
            for k,v in kwargs.items():
                if k in ["lang"]:
                    user.settings[k] = v
            sess.commit()
        return True

    @cherrypy.expose
    def login(self, username = None, password = None, redirectto="/"):
        url = inspect.stack()[0][3]
        if cherrypy.request.method == "POST" and all([username, password]):
            if self._login(username,password):
                raise HTTPRedirect(redirectto)
            return self.serve_site("auth/%s" % url, url = url, state = "failed", redirectto = redirectto)
        return self.serve_site("auth/%s" % url, url = url, redirectto = redirectto)

    @cherrypy.expose
    def register(self, username = None, email = None, email_again = None, state=None, me=None, url=None, **kwargs):
        url = inspect.stack()[0][3]
        if cherrypy.request.method == "POST" and all([username, email, email_again]):
            state = self._register(username, email, email_again, **kwargs)
            if state is True:
                return self.serve_site("auth/register_next", url = url, state = state, username = username, email = email, **kwargs)
            return self.serve_site("auth/%s" % url, url = url, state = state, username = username, email = email, **kwargs)
        return self.serve_site("auth/%s" % url, url = url )

    @cherrypy.expose
    def reset_password(self, username=None, email=None ):
        url = inspect.stack()[0][3]
        if cherrypy.request.method == "POST" and all([username, email]):
            with tsdb.getSess() as sess:
                sess.begin()
                user = sess.execute( select(tsdb.User)
                    .where(tsdb.User.username == username)
                    .where(tsdb.User.email == email)
                    .where(tsdb.User.active == True)
                ).scalar_one_or_none()
                if user:
                    user.pwtoken = secrets.token_urlsafe(256)
                    user.pwtokenexpire = dt.datetime.now(dt.timezone.utc) + dt.timedelta(days = 1)
                    user.mails.append("pwreset")
                    sess.commit()
            return self.serve_site("auth/reset_password_next", url = url )
        return self.serve_site("auth/%s" % url, url = url )

    @cherrypy.expose
    def change_password(self, old_password=None, new_password=None, new_password_again=None, redirectto="/"):
        url = inspect.stack()[0][3]
        user = self.get_user()
        state = None
        if user and user.pwhash:
            if cherrypy.request.method == "POST" and all([old_password, new_password, new_password_again]):
                if new_password != new_password_again:
                    state = "pw_nomatch"
                elif not self._check_password(user.pwhash, bytes(old_password,"utf-8")):
                    state = "pw_failed"
                else:
                    ph = PasswordHasher()
                    with tsdb.getSess() as sess:
                        sess.begin()
                        user = sess.get(tsdb.User, {"userid":user.userid})
                        user.pwhash = ph.hash(bytes(new_password,"utf-8"))
                        sess.commit()
                    raise HTTPRedirect(redirectto)
            return self.serve_site("auth/%s" % url, url = url, user = user, state = state, redirectto = redirectto)
        else:
            raise HTTPRedirect(redirectto)

    @cherrypy.expose
    def set_password(self, pwtoken, password=None, password_again=None, redirectto="/"):
        url = inspect.stack()[0][3]
        state = None
        if cherrypy.request.method == "POST" and all([password, password_again]):
            with tsdb.getSess() as sess:
                sess.begin()
                user = sess.execute( select(tsdb.User)
                    .where(tsdb.User.active == True)
                    .where(tsdb.User.pwtoken == pwtoken)
                    .where(tsdb.User.pwtokenexpire >= dt.datetime.now(dt.timezone.utc))
                ).scalar_one_or_none()
                if user:
                    if password == password_again:
                        ph = PasswordHasher()
                        user.pwhash = ph.hash(bytes(password,"utf-8"))
                        user.pwtoken = None
                        user.pwtokenexpire = None
                        sess.commit()
                        raise HTTPRedirect(redirectto)
                    else:
                        state = "pw_nomatch"
        return self.serve_site("auth/%s" % url, url = url, pwtoken = pwtoken, state = state, redirectto = redirectto)

    @cherrypy.expose
    def logout(self,redirectto="/"):
        if "sessid" in cherrypy.request.cookie:
            sessid = cherrypy.request.cookie["sessid"].value
            with tsdb.getSess() as sess:
                s = sess.get(tsdb.Session, {"sessid":sessid})
                if s:
                    sess.delete(s)
                    sess.commit()
            cookie = cherrypy.response.cookie
            cookie['sessid'] = ""
            cookie['sessid']['path'] = '/'
            cookie['sessid']['max-age'] = 0
            cookie['sessid']['version'] = 1
        raise HTTPRedirect(redirectto)

    def get_user(self):
        if "sessid" in cherrypy.request.cookie:
            sessid = cherrypy.request.cookie["sessid"].value
            with tsdb.getSess() as sess:
                res = sess.execute( delete(tsdb.Session).where(tsdb.Session.expire < dt.datetime.now(dt.timezone.utc)) )
                sess.commit()
                s = sess.get(tsdb.Session, {"sessid":sessid})
                if s:
                    cookie = cherrypy.response.cookie
                    cookie['sessid'] = sessid
                    cookie['sessid']['path'] = '/'
                    cookie['sessid']['max-age'] = 24*60*60
                    cookie['sessid']['version'] = 1
                    return s.user
        return None
