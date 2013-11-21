import sqlalchemy as sa
import sqlalchemy.exc
import time

metadata = sa.MetaData()

repositories = sa.Table('repositories', metadata,
    sa.Column('repoid', sa.Integer, nullable=False, primary_key=True),
    sa.Column('name', sa.Text, nullable=False, unique=True),
    sa.Column('url', sa.Text, nullable=False),
)
users = sa.Table('users', metadata,
    sa.Column('userid', sa.Integer, nullable=False, primary_key=True),
    sa.Column('canonical_email', sa.String(128), nullable=False, unique=True),
)
user_emails = sa.Table('user_emails', metadata,
        sa.Column('userid', sa.Integer,
            sa.ForeignKey('users.userid'),
            nullable=False),
    sa.Column('email', sa.String(128), nullable=False),
)
revisions = sa.Table('revisions', metadata,
    sa.Column('repoid', sa.Integer,
        sa.ForeignKey('repositories.repoid'),
        nullable=False),
    sa.Column('revision', sa.String(40), nullable=False),
    sa.Column('author', sa.Integer,
        sa.ForeignKey('users.userid'),
        nullable=False),
    sa.Column('lines_added', sa.Integer, nullable=False),
    sa.Column('lines_removed', sa.Integer, nullable=False),
    sa.Column('when', sa.Integer, nullable=False),
)

sa.Index('unique_rev',
    revisions.c.repoid,
    revisions.c.revision,
    unique=True)

sa.Index('when_rev',
    revisions.c.when)


class DB(object):

    def __init__(self, url):
        self.engine = sa.create_engine(url)
        metadata.bind = self.engine
        metadata.create_all(self.engine, checkfirst=True)

    @property
    def conn(self):
        return self.engine.connect()

    def get_repoid(self, name, url):
        conn = self.conn
        res = conn.execute(
                repositories.select(repositories.c.name==name))
        res = res.scalar()
        if not res:
            ins = repositories.insert({'name': name, 'url': url})
            res = conn.execute(ins)
            return res.lastrowid
        else:
            return res

    def get_userid(self, email):
        conn = self.conn
        res = conn.execute(
                user_emails.select(user_emails.c.email==email))
        res = res.scalar()
        if res:
            return res

        # insert into users to get a unique userid, and use that           
        ins = users.insert({'canonical_email': email})                     
        res = conn.execute(ins)                                     
        userid = res.lastrowid                                             
                                                                          
        ins = user_emails.insert({'userid': userid, 'email': email})       
        conn.execute(ins)                                           
        return userid                                                      

    def get_users(self):
        res = self.conn.execute(
                users.join(user_emails).select(use_labels=1,
                                               order_by=users.c.userid))
        rv = []
        current_row = None
        last_userid = None
        for row in res:
            if row[users.c.userid] != last_userid:
                last_userid = row['users_userid']
                current_row = [row[users.c.canonical_email]]
                rv.append(current_row)
            email = row[user_emails.c.email]
            if email not in current_row:
                current_row.append(email)
        rv.sort()
        return rv

    def merge_users(self, merge_from, merge_to):
        conn = self.conn

        from_userid = self.get_userid(merge_from)
        to_userid = self.get_userid(merge_to)
        if from_userid != to_userid:
            conn.execute(
                user_emails.update(
                    whereclause=user_emails.c.userid==from_userid),
                userid=to_userid)

            # fix revision ownership
            conn.execute(
                revisions.update(
                    whereclause=revisions.c.author==from_userid),
                author=to_userid)

            # delete the old user record
            conn.execute(
                users.delete(
                    whereclause=users.c.userid==from_userid))

        # and update the canonical address for the new record
        conn.execute(
            users.update(
                whereclause=users.c.userid==to_userid),
            canonical_email=merge_to)

    def add_revision(self, repoid, rev):
        # first, get the author's userid
        userid = self.get_userid(rev.author)
        assert userid is not None
        try:
            ins = revisions.insert({
                'repoid': repoid,
                'revision': rev.revision,
                'author': userid,
                'lines_added': rev.added,
                'lines_removed': rev.removed,
                'when': rev.when,
            })
            self.conn.execute(ins)
        except sqlalchemy.exc.IntegrityError:
            pass

    def changes_by_user_repo(self, since):
        fields = [
            revisions.c.repoid, revisions.c.author,
            sa.func.sum(revisions.c.lines_added).label('lines_added'),
            sa.func.sum(revisions.c.lines_removed).label('lines_removed'),
        ]
        q = sa.select(fields)
        q = q.group_by(revisions.c.repoid, revisions.c.author)
        q = q.where(revisions.c.when > since)
        res = self.conn.execute(q)

        # now translate userids to canonical userids, and repos to names,
        # and make a dictionary out of it
        email_cache = {}
        repo_cache = {}
        rv = {}
        for row in res:
            if row.author not in email_cache:
                email_cache[row.author] = sa.select(
                        [users.c.canonical_email],
                        users.c.userid==row.author).scalar()
            email = email_cache[row.author]
            if row.repoid not in repo_cache:
                repo_cache[row.repoid] = sa.select(
                        [repositories.c.name],
                        repositories.c.repoid==row.repoid).scalar()
            repo = repo_cache[row.repoid]
            rv.setdefault(email, {})[repo] = (row.lines_added,
                                              row.lines_removed)
        return rv
