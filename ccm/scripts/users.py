import ccm.vcs
import ccm.scripts.base

def main():
    def extra_args(parser):
        subs = parser.add_subparsers(help='sub-commands')
        list_parser = subs.add_parser('list',
                description='list users',
                help='list users')
        list_parser.set_defaults(action='list')
        merge_parser = subs.add_parser('merge',
                description='merge emails',
                help='merge emails into a single user')
        merge_parser.set_defaults(action='merge')
        merge_parser.add_argument('merge_to', metavar='TO',
                nargs=1, help="user's canonical email")
        merge_parser.add_argument('merge_from', metavar='FROM',
                nargs='+', help='emails to merge into TO')
    db, logger, parser, args, cfg = ccm.scripts.base.set_up(
            'ccm-users',
            'Manipulate users',
            extra_args)

    if args.action == 'list':
        for user in db.get_users():
            # canonical email is listed first
            canonical = user[0]
            print canonical
            for email in user[1:]:
                print "  Alias: %s" % email

    elif args.action == 'merge':
        for merge_from in args.merge_from:
            db.merge_users(merge_from=merge_from,
                    merge_to=args.merge_to[0])

