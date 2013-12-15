import calendar
import time
import approxidate
import datetime
import unittest

def datearg(str):
    # return midnight, UTC, of the given date
    ts = approxidate.approx(str)
    # approxidate uses the current *local* time, but we only want the date, so
    # convert from unix timestamp back to a tuple
    tup = time.localtime(ts)
    # and use the first three elements of that tuple
    return calendar.timegm((tup[0], tup[1], tup[2], 0, 0, 0, 0, 0, 0))

def datearg_plus(str):
    # return the end of the given day
    return datearg(str) + 3600*24-1

def to_date(timestamp):
    return time.strftime('%Y-%m-%d', time.gmtime(timestamp))

class Tests(unittest.TestCase):

    def test_datearg(self):
        self.assertEqual(time.gmtime(datearg('nov 10 2013'))[:6], (2013, 11, 10, 0, 0, 0))

    def test_datearg_plus(self):
        self.assertEqual(time.gmtime(datearg_plus('nov 10 2013'))[:6], (2013, 11, 10, 23, 59, 59))

    def test_to_date(self):
        self.assertEqual(to_date(datearg('nov 10 2013')), '2013-11-10')
