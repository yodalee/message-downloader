# -*- coding: utf-8 -*-
import time
import logging
from datetime import datetime
from lxml import etree
from io import BytesIO

from config import REdict
from dbSqlite3 import dbSqlite3

database = dbSqlite3()

class ParseHandler():
    def __init__(self):
        self.xpathContent = etree.XPath("//div[@class='contents']")
        self.xpathUser    = etree.XPath(".//h1//text()")
        self.xpathThread  = etree.XPath(".//div[@class='thread']")
        self.xpathMessage = etree.XPath(".//div[@class='message']")
        self.xpathAuthor  = etree.XPath(".//span[@class='user']//text()")
        self.xpathTime    = etree.XPath(".//span[@class='meta']//text()")
        self.xpathText    = etree.XPath(".//p")
        self.lang = None

    def setLang(self, lang):
        self.lang = REdict[lang]

    def simpleCheck(self, file_content):
        logging.info("initial parse check: {}".format(self.lang["showName"]))

        parser = etree.HTMLParser(encoding='UTF-8')
        root = etree.parse(BytesIO(file_content), parser)

        # process group
        content = self.xpathContent(root)[0]

        # start processing
        thread = self.xpathThread(content)[0]
        timetext = self.xpathTime(thread)[0]
        timetext = timetext.strip().rsplit(" ", 1)[0]
        msgtime = datetime.strptime(timetext, self.lang["parseStr"])

    def parseUsername(self, file_content):
        parser = etree.HTMLParser(encoding='UTF-8')
        root = etree.parse(BytesIO(file_content), parser)
        content = self.xpathContent(root)[0]
        username = self.xpathUser(content)[0].strip()

        logging.info("Parse username: {}".format(username))

        return username

    def parse(self, userid):
        logging.info("user_id: {}, lang: {}".format(userid, self.lang["showName"]))

        s = database.getUpload(userid)

        # prepare parser
        parser = etree.HTMLParser(encoding='UTF-8')
        root = etree.parse(BytesIO(s), parser)
        content = self.xpathContent(root)[0]
        threads = self.xpathThread(content)

        # process group
        existGroup = database.getGroup(userid)
        grouplist = dict()
        for (groupid, members) in existGroup:
            grouplist[members] = groupid
        groupnum = len(threads)

        # variable
        processed = 0
        idx = 0
        msgbuf = [None] * 512
        subtime = 0
        prevtime = datetime(2001, 1, 1)

        # process group, user name
        for thread in threads:
            members = thread.text.strip()

        # start processing message
        print("Process start")
        starttime = time.time()

        for thread in threads:
            members = thread.text.strip()

            if members in grouplist:
                groupid = grouplist[members]
            else:
                groupid = database.insertGroup(userid, members)
                grouplist[members] = groupid

            print("Process id {}: {}, progress {}/{}".format(
                groupid, members, processed, groupnum))

            authorlist = self.xpathAuthor(thread)
            timelist = self.xpathTime(thread)
            textlist = self.xpathText(thread)

            for author, timetext, text in zip(authorlist, timelist, textlist):
                author = author.strip()

                # cut down last string "UTC+08"
                # which cause dateparser failed to parse
                timetext = timetext.strip().rsplit(" ", 1)[0]
                msgtime = datetime.strptime(timetext, self.lang["parseStr"])
                if msgtime == prevtime:
                    subtime = subtime + 1
                else:
                    prevtime = msgtime
                    subtime = 0
                text = (text.text or "").strip()

                msgbuf[idx] = (groupid, author, msgtime, subtime, text)

                idx = idx + 1
                if idx == 512:
                    idx = 0
                    database.insertMessage(msgbuf)

            processed = processed + 1

        if idx != 0:
            database.insertMessage(msgbuf[:idx])

        # process end
        endtime = time.time()
        print("Process end, time consumed: {}".format(endtime-starttime))

        # update user info
        database.updateUser(userid)
