import argparse
import logging
import os
import ConfigParser
import datetime
import calendar
import time
import ccm.db
import ccm.util

def add_args_days_start_end(parser):
    parser.add_argument('--days', metavar='DAYS',
            type=int, help='number of days to address (equivalent to --start and --end)')
    parser.add_argument('--start',
            type=ccm.util.datearg, help='first date to work on')
    parser.add_argument('--end',
            type=ccm.util.datearg_plus, help='last date to work on')

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

def set_up(name, description, extra_args):
    parser = argparse.ArgumentParser(
            description=description)
    parser.add_argument('--verbose', dest='verbose', action='store_true',
            help='be verbose')
    parser.add_argument('--config', dest='config', default='ccm.ini',
            help='path to configuration file')
    extra_args(parser)
    args = parser.parse_args()

    level = logging.WARNING if not args.verbose else logging.DEBUG
    logging.basicConfig(format="%(asctime)s %(name)s %(message)s",
            level=level)
    if args.verbose:
        logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
    logger = logging.getLogger(name)

    cfg = ConfigParser.SafeConfigParser()
    cfg.read([args.config])

    os.chdir(cfg.get('main', 'basedir'))

    db = ccm.db.DB(cfg.get('main', 'db'))
    return db, logger, parser, args, cfg

