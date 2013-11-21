import time
import sys
import csv
import itertools
import ccm.vcs
import ccm.scripts.base

def main():
    def extra_args(parser):
        parser.add_argument('--days', metavar='DAYS',
                type=int, help='number of days over which to report',
                default=1)
        parser.add_argument('--format', help='report format',
                default='html', choices=('html', 'csv'))
    db, logger, parser, args, cfg = ccm.scripts.base.set_up(
            'ccm-reports',
            'Generate reports',
            extra_args)

    # first, generate an actual rectangular array of data, along with
    # row and column titles
    grid = db.changes_by_user_repo(days_back=args.days)
    users = grid.keys()
    users.sort()
    repos = list(reduce(lambda x, y: x.union(y), [
        row.keys() for row in grid.values()
    ], set()))
    repos.sort()
    grid = [ [ grid[u].get(r, (0,0)) for r in repos ] for u in users ]

    if args.format == 'html':
        output_html(grid, users, repos, args)
    elif args.format == 'csv':
        output_csv(grid, users, repos, args)
    else:
        parser.error("unknown format %s" % format)

def grid_sum(cells):
    def add(tup1, tup2):
        return tup1[0]+tup2[0], tup1[1]+tup2[1]
    return reduce(add, cells, (0,0))

def output_html(grid, users, repos, args):
    def pm(tup):
        if tup[0] == tup[1] == 0:
            return ''
        return "<span class='plus'>+%s</span>/<span class='minus'>-%s</span>" % tup

    start_date = time.asctime(time.localtime(time.time() - args.days*3600*24))
    end_date = time.asctime(time.localtime(time.time()))
    print "<html><head>"
    print "<title>Code Changes by User and Repo</title>"
    print "<style>span.plus { color: green; }</style>"
    print "<style>span.minus { color: red; }</style>"
    print "</head>"
    print "<body>"
    print "<h1>Code Changes by User and Repo</h1>"
    print "<h2>From %s to %s</h2>" % (start_date, end_date)
    print "<table border='1'>"
    print "<tr><th>user</th>"
    for repo in repos:
        print " <th>%s</th>" % repo
    print " <th>total</th>"
    print "</tr>"
    for user, row in itertools.izip(users, grid):
        print "<tr><th>%s</th>" % user
        for cell in row:
            print " <td>%s</td>" % pm(cell)
        print " <td>%s</td>" % pm(grid_sum(row))
        print "</tr>"
    print "<tr><th>total</th>"
    for r in xrange(len(repos)):
        print " <th>%s</th>" % pm(grid_sum(grid[u][r] for u in xrange(len(users))))
    print " <th>%s</th>" % pm(grid_sum(grid_sum(grid[u][r] for u in xrange(len(users))) for r in xrange(len(repos))))
    print "</tr>"
    print "</table>"
    print "</body>"
    print "</html>"

def output_csv(grid, users, repos, args):
    w = csv.writer(sys.stdout)
    def flatten(l):
        return itertools.chain.from_iterable(l)
    w.writerow([''] + list(flatten(('+'+r, '-'+r) for r in repos)))

    for user, row in itertools.izip(users, grid):
        w.writerow([user] + list(flatten(row)))
