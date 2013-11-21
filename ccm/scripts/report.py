import sys
import csv
import calendar
import itertools
import datetime
import ccm.vcs
import cStringIO
import ccm.scripts.base
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

def main():
    def extra_args(parser):
        parser.add_argument('--days', metavar='DAYS',
                type=int, help='number of days over which to report',
                default=1)
        parser.add_argument('--format', help='report format',
                default='html', choices=('html', 'csv', 'email'))
    db, logger, parser, args, cfg = ccm.scripts.base.set_up(
            'ccm-report',
            'Generate a report',
            extra_args)

    since = datetime.date.today() - datetime.timedelta(days=args.days)
    # yeah, really..
    since_epoch = calendar.timegm(datetime.datetime.combine(since, datetime.datetime.min.time()).utctimetuple())

    # generate an actual rectangular array of data, along with row and column
    # titles
    grid = db.changes_by_user_repo(since=since_epoch)
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
    output_fn(grid, users, repos, since, parser, args, cfg, sys.stdout)

def grid_sum(cells):
    def add(tup1, tup2):
        return tup1[0]+tup2[0], tup1[1]+tup2[1]
    return reduce(add, cells, (0,0))

def output_html(grid, users, repos, since, parser, args, cfg, outfile):
    def pm(tup):
        if tup[0] == tup[1] == 0:
            return ''
        return "<span class='plus'>+%s</span>/<span class='minus'>-%s</span>" % tup

    end_date = datetime.date.today()
    print >>outfile, "<html><head>"
    print >>outfile, "<title>Code Changes by User and Repo</title>"
    print >>outfile, "<style>span.plus { color: green; }</style>"
    print >>outfile, "<style>span.minus { color: red; }</style>"
    print >>outfile, "</head>"
    print >>outfile, "<body>"
    print >>outfile, "<h1>Code Changes by User and Repo</h1>"
    print >>outfile, "<h2>From %s to %s</h2>" % (since, end_date)
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

def output_csv(grid, users, repos, since, parser, args, cfg, outfile):
    w = csv.writer(outfile)
    def flatten(l):
        return itertools.chain.from_iterable(l)
    w.writerow(['since %s' % (since,)]
            + list(flatten(('+'+r, '-'+r) for r in repos)))

    for user, row in itertools.izip(users, grid):
        w.writerow([user] + list(flatten(row)))

def output_email(grid, users, repos, since, parser, args, cfg, oufile):
    email_from = cfg.get('reports', 'email-from')
    email_to = cfg.get('reports', 'email-to').split()
    f = cStringIO.StringIO()
    output_csv(grid, users, repos, since, parser, args, cfg, f)
    csv_data = f.getvalue()

    f = cStringIO.StringIO()
    output_html(grid, users, repos, since, parser, args, cfg, f)
    html_data = f.getvalue()

    msg = MIMEMultipart()
    msg['Subject'] = "Code Changed since %s" % since
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
