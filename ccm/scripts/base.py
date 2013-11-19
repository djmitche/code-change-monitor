import argparse
import logging
import os
import ConfigParser
import ccm.db

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

