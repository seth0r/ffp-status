#!/usr/bin/env python3
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.mime.text import MIMEText
from email.utils import formatdate, make_msgid
import os

class Mail:
    def __init__(self, msgsender, logger):
        self.msgsender = msgsender
        self.logger = logger

    def emit(self, **kwargs):
        msg = MIMEMultipart()
        receivers = kwargs["receivers"]
        tplrender = self.msgsender.render( kwargs["tpl"], **kwargs )
        if "\n\n\n" in tplrender:
            subject,_,text = tplrender.partition("\n\n\n")
        else:
            subject = "No Subject"
            text = tplrender
        msg["From"] = os.getenv("MAIL_FROM_ADDRESS")
        msg["To"] = ", ".join( receivers )
        msg["Subject"] = " ".join( subject.split("\n") )
        msg["Date"] = formatdate()
        msg["Message-ID"] = make_msgid()
        msg.attach(MIMEText( text, _charset='utf-8' ))

        if os.getenv("MAIL_SSL","").lower() in ["true","1","on","yes"]:
            smtp = smtplib.SMTP_SSL( os.getenv("MAIL_HOST"), int(os.getenv("MAIL_PORT")) )
        else:
            smtp = smtplib.SMTP( os.getenv("MAIL_HOST"), int(os.getenv("MAIL_PORT")) )
            if os.getenv("MAIL_STARTTLS","").lower() in ["true","1","on","yes"]:
                smtp.starttls()
        smtp.login( os.getenv("MAIL_USER"), os.getenv("MAIL_PASSWORD") )
        try:
            res = smtp.send_message(msg)
        except smtplib.SMTPRecipientsRefused as ex:
            errors = {}
            for k,v in ex.recipients.items():
                self.logger.error( "Sending mail to {} failed: {} {}".format( k,v[0],v[1].decode('utf-8') ))
        except smtplib.SMTPSenderRefused as ex:
            self.logger.error( "Sending mail from {} failed.".format( msg["From"] ))
        else:
            if len(receivers) > len(res):
                self.logger.info( "Sending mail to {} successful.".format(", ".join( set(receivers) - set(res.keys()) )))
            for k,v in res.items():
                self.logger.warning( "Sending mail to {} failed: {} {}".format( k,v[0],v[1].decode('utf-8') ))
            return True
        finally:
            smtp.quit()
