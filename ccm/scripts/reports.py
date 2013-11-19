import time
import ccm.vcs
import ccm.scripts.base

def main():
    def extra_args(parser):
        parser.add_argument('--days', metavar='DAYS',
                type=int, help='number of days over which to report',
                default=1)
    db, logger, parser, args, cfg = ccm.scripts.base.set_up(
            'ccm-reports',
            'Generate reports',
            extra_args)

    grid = db.changes_by_user_repo(days_back=args.days)
    users = grid.keys()
    users.sort()
    repos = list(reduce(lambda x, y: x.union(y), [
        row.keys() for row in grid.values()
    ], set()))
    repos.sort()

    def add(tup1, tup2):
        return tup1[0]+tup2[0], tup1[1]+tup2[1]

    start_date = time.asctime(time.localtime(time.time() - args.days*3600*24))
    end_date = time.asctime(time.localtime(time.time()))
    print "<html><head><title>Code Changes by User and Repo</title></head>"
    print "<body>"
    print "<h1>Code Changes by User and Repo</h1>"
    print "<h2>From %s to %s</h2>" % (start_date, end_date)
    print "<table>"
    print "<tr><th>user</th>"
    for repo in repos:
        print " <th>%s</th>" % repo
    print " <th>total</th>"
    print "</tr>"
    total_per_repo = {}
    for user in users:
        print "<tr><th>%s</th>" % user
        total = (0, 0)
        for repo in repos:
            count = grid[user].get(repo)
            if count:
                total = add(total, count)
                total_per_repo[repo] = \
                    add(total_per_repo.get(repo, (0,0)), count)
                count = '+%s/-%s' % count
            else:
                count = ''
            print " <td>%s</td>" % count
        print " <td>+%s/-%s</td>" % total
        print "</tr>"
    print "<tr><th>total</th>"
    for repo in repos:
        print " <th>+%s/-%s</th>" % total_per_repo[repo]
    print " <th>+%s/-%s</th>" % reduce(add, total_per_repo.values(), (0,0))
    print "</tr>"
    print "</table>"
    print "</body>"
    print "</html>"
