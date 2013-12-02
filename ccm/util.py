import calendar
import time
import approxidate
import datetime

def add_args_days_start_end(parser):
    def datearg(str):
        # return midnight, UTC, of the given date
        ts = approxidate.approx(str)
        tup = time.gmtime(ts)
        return calendar.timegm((tup[0], tup[1], tup[2], 0, 0, 0, 0, 0, 0))
    def datearg_plus(str):
        # return the end of the given day
        return datearg(str) + 3600*24-1
    parser.add_argument('--days', metavar='DAYS',
            type=int, help='number of days to address (equivalent to --start and --end)')
    parser.add_argument('--start',
            type=datearg, help='first date to work on')
    parser.add_argument('--end',
            type=datearg_plus, help='last date to work on')

def handle_args_days_start_end(parser, args):
    if args.days is None and args.start is None:
        args.days = 1
    if args.start is not None:
        if args.days is not None:
            parser.error("specify either --days or --start, not both")
    else:
        start = datetime.date.today() - datetime.timedelta(days=args.days)
        args.start = calendar.timegm(
                datetime.datetime.combine(start,
                                          datetime.datetime.min.time()).utctimetuple())

    if args.end is None:
        # end now
        args.end = time.time()

def to_date(timestamp):
    return time.strftime('%Y-%m-%d', time.gmtime(timestamp))

