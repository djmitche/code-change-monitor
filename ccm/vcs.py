import abc
import logging
import subprocess
import re
import os

class Rev(object):

    def __init__(self):
        self.revision = self.author = None
        self.when = None
        self.added = self.removed = 0

    def __repr__(self):
        return `self.revision, self.author, self.added, self.removed, self.when`


class Repository(object):

    __metaclass__ = abc.ABCMeta

    def __init__(self, name, url, local_path):
        self.name = name
        self.url = url
        self.local_path = local_path
        self.logger = logging.getLogger('repo.%s' % self.name)

    def __str__(self):
        return self.url

    @abc.abstractmethod
    def update(self):
        pass

    @abc.abstractmethod
    def enumerate_recent_revisions(self, days):
        pass


class Git(Repository):

    def update(self):
        # clone if necessary
        if not os.path.isdir(self.local_path):
            self.logger.info('cloning')
            subprocess.check_call(['git', 'clone', '--quiet',
                                   self.url, self.local_path])
        else:
            self.logger.info('updating')
            subprocess.check_call(['git', 'pull', '--quiet'],
                cwd=self.local_path)

    def enumerate_recent_revisions(self, days):
        self.logger.info('enumerating revisions from the last %d days' % days)
        out = subprocess.check_output(['git', 'log', '--since', '%d days' % days,
                                       '--format=format:%H %ct %aE', '--shortstat'],
            cwd=self.local_path)
        out = out.split('\n')

        hash_re = re.compile(r'^([a-z0-9]{40}) (\d+) ([^ ]+)')
        shortstat_re = re.compile(r'\s*\d+ files? changed(, (\d+) insertions?...)?(, (\d+) deletions?...)?')
        rv = []
        while out:
            line = out.pop(0)
            mo = hash_re.match(line)
            if mo:
                rv.append(Rev())
                rv[-1].revision, rv[-1].when, rv[-1].author = mo.groups()
            mo = shortstat_re.match(line)
            if mo:
                if mo.group(2):
                    rv[-1].added = int(mo.group(2))
                if mo.group(4):
                    rv[-1].removed = int(mo.group(4))
        return rv


def load_all(cfg):
    basedir = cfg.get('main', 'basedir')
    repos = os.path.join(basedir, 'repos')
    if not os.path.exists(repos):
        os.makedirs(repos)

    for name, url in cfg.items('git'):
        path = os.path.join(basedir, 'repos', name)
        yield Git(name, url, path)
