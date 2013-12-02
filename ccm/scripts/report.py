import time
import sys
import csv
import calendar
import itertools
import datetime
import ccm.vcs
import cStringIO
import ccm.scripts.base
import approxidate
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


def main():
    def extra_args(parser):
        def datearg(str):
            # return midnight, UTC, of the given date
            ts = approxidate.approx(str)
            tup = time.gmtime(ts)
            return calendar.timegm((tup[0], tup[1], tup[2], 0, 0, 0, 0, 0, 0))
        def datearg_plus(str):
            # return the end of the given day
            return datearg(str) + 3600*24-1
        parser.add_argument('--days', metavar='DAYS',
                type=int, help='number of days over which to report (equivalent to --start and --end)')
        parser.add_argument('--start',
                type=datearg, help='first date of report')
        parser.add_argument('--end',
                type=datearg_plus, help='last date of report')
        parser.add_argument('--format', help='report format',
                default='html', choices=('html', 'csv', 'email'))
    db, logger, parser, args, cfg = ccm.scripts.base.set_up(
            'ccm-report',
            'Generate a report',
            extra_args)

    if args.days is None and args.start is None:
        args.days = 1
    if args.start is not None:
        if args.days is not None:
            parser.error("specify either --days or --start, not both")
    else:
        start = datetime.date.today() - datetime.timedelta(days=args.days)
        args.start = calendar.timegm(datetime.datetime.combine(start, datetime.datetime.min.time()).utctimetuple())

    if args.end is None:
        # end now
        args.end = time.time()

    # generate an actual rectangular array of data, along with row and column
    # titles
    grid = db.changes_by_user_repo(start=args.start, end=args.end)
    users = grid.keys()
    users.sort()
    repos = list(reduce(lambda x, y: x.union(y), [
        row.keys() for row in grid.values()
    ], set()))
    repos.sort()
    grid = [ [ grid[u].get(r, (0,0)) for r in repos ] for u in users ]

    # call the output function
    output_fn = {
        'html': output_html,
        'csv': output_csv,
        'email': output_email,
    }[args.format]
    output_fn(grid, users, repos, parser, args, cfg, sys.stdout)

def to_date(timestamp):
    return time.strftime('%Y-%m-%d', time.gmtime(timestamp))

def grid_sum(cells):
    def add(tup1, tup2):
        return tup1[0]+tup2[0], tup1[1]+tup2[1]
    return reduce(add, cells, (0,0))

def output_html(grid, users, repos, parser, args, cfg, outfile):
    def pm(tup):
        if tup[0] == tup[1] == 0:
            return ''
        return "<span class='plus'>+%s</span>/<span class='minus'>-%s</span>" % tup

    print >>outfile, "<html><head>"
    print >>outfile, "<title>Code Changes by User and Repo</title>"
    print >>outfile, "<style>span.plus { color: green; }</style>"
    print >>outfile, "<style>span.minus { color: red; }</style>"
    print >>outfile, "</head>"
    print >>outfile, "<body>"
    print >>outfile, "<h1>Code Changes by User and Repo</h1>"
    print >>outfile, "<h2>From %s through %s</h2>" % (to_date(args.start), to_date(args.end))
    print >>outfile, "<table border='1'>"
    print >>outfile, "<tr><th>user</th>"
    for repo in repos:
        print >>outfile, " <th>%s</th>" % repo
    print >>outfile, " <th>total</th>"
    print >>outfile, "</tr>"
    for user, row in itertools.izip(users, grid):
        print >>outfile, "<tr><th>%s</th>" % user
        for cell in row:
            print >>outfile, " <td>%s</td>" % pm(cell)
        print >>outfile, " <td>%s</td>" % pm(grid_sum(row))
        print >>outfile, "</tr>"
    print >>outfile, "<tr><th>total</th>"
    for r in xrange(len(repos)):
        print >>outfile, " <th>%s</th>" % pm(grid_sum(grid[u][r] for u in xrange(len(users))))
    print >>outfile, " <th>%s</th>" % pm(grid_sum(grid_sum(grid[u][r] for u in xrange(len(users))) for r in xrange(len(repos))))
    print >>outfile, "</tr>"
    print >>outfile, "</table>"
    print >>outfile, "</body>"
    print >>outfile, "</html>"

def output_csv(grid, users, repos, parser, args, cfg, outfile):
    w = csv.writer(outfile)
    def flatten(l):
        return itertools.chain.from_iterable(l)
    w.writerow(['%s through %s' % (to_date(args.start), to_date(args.end))]
            + list(flatten(('+'+r, '-'+r) for r in repos)))

    for user, row in itertools.izip(users, grid):
        w.writerow([user] + list(flatten(row)))

def output_email(grid, users, repos, parser, args, cfg, oufile):
    email_from = cfg.get('reports', 'email-from')
    email_to = cfg.get('reports', 'email-to').split()
    f = cStringIO.StringIO()
    output_csv(grid, users, repos, parser, args, cfg, f)
    csv_data = f.getvalue()

    f = cStringIO.StringIO()
    output_html(grid, users, repos, parser, args, cfg, f)
    html_data = f.getvalue()

    msg = MIMEMultipart()
    msg['Subject'] = "Code Changed %s through %s" % (to_date(args.start), to_date(args.end))
    msg['From'] = email_from
    msg['To'] = ', '.join(email_to)

    msg.attach(MIMEText(html_data, 'html'))

    att = MIMEText(csv_data, 'csv')
    att.add_header('Content-Disposition', 'attachment; filename="ccm-%s.csv"' % datetime.date.today())
    msg.attach(att)

    # Send the message via local SMTP server.
    s = smtplib.SMTP('localhost')
    # sendmail function takes 3 arguments: sender's address, recipient's address
    # and message to send - here it is sent as one string.
    s.sendmail(email_from, email_to, msg.as_string())
    s.quit()
