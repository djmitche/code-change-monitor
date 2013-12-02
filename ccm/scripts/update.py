import ccm.util
import ccm.vcs
import ccm.scripts.base

def main():
    def extra_args(parser):
        parser.add_argument('--repository',
                help='repository to scan; defaults to all')
        ccm.util.add_args_days_start_end(parser)
    db, logger, parser, args, cfg = ccm.scripts.base.set_up(
            'ccm-update',
            'Update version-control repositories',
            extra_args)

    ccm.util.handle_args_days_start_end(parser, args)

    for repo in ccm.vcs.load_all(cfg):
        if args.repository and repo.name != args.repository:
            continue
        logger.info('processing %s' % repo)
        repo.update()
        repoid = db.get_repoid(repo.name, repo.url)
        # TODO: go back until the last time this was successfully
        # processed, and store that info, if no date info is given
        for rev in repo.enumerate_recent_revisions(args.start, args.end):
            # skip merges
            if rev.added or rev.removed:
                db.add_revision(repoid, rev)
