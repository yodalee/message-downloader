#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import datetime

from config import REdict, REdictTest

class REdictParseTest(unittest.TestCase):
    pass

def testParseGen(k, v):
    def test(self):
        timetext = REdictTest[k]["q"].rsplit(" ", 1)[0]
        parse = datetime.datetime.strptime(timetext, v["parseStr"])
        ans = REdictTest[k]["a"]
        assert(ans == parse)
    return test

def main():
    for k,v in REdict.items():
        test_func = testParseGen(k, v)
        setattr(REdictParseTest, "test_%s" % (k), test_func)
    unittest.main()

if __name__ == "__main__":
    main()
