code-change-monitor
===================

Simple tool to count changes per developer in version control systems

Running
-------

### Requirements:

* Python-2.7
* Modern git (newer than 1.7, maybe higher)
* svn

If you're using ssh+svn, you'll need an SSH key loaded into an agent, too.
Subversion doesn't have a way to specify a particular key, unfortunately.

### Setup

Create a new virtualenv, named `ccm`, wherever you'd like it.

    $ virtualenv --python=python2.7 ccm
    $ cd ccm
    $ ./bin/pip install git+https://github.com/djmitche/code-change-monitor.git#egg=code-change-monitor

This should install a number of packages from pypi and finish successfully.

### Configuration

Copy https://raw.github.com/djmitche/code-change-monitor/master/ccm.ini.sample to `ccm.ini`
Edit the `[git]  and `[svn]` sections to reflect the repositories you want to monitor.

### Usage

The general plan is to update the local DB with changes in version control repositories periodically, and then create reports from the DB.

To update the DB with recent changes, in this example from the last two days:

    $ ./bin/ccm-update --days 2

(see ccm-update --help for more)

To generate a report:

    $ ./bin/ccm-report --start 'nov 1' --end 'nov 31'

(see --help here, too; --format email will email the people listed in `[reports]` in `ccm.ini`)

If you see multiple instances of the same user with different emails, you can merge them:

    $ ccm-users merge dustin@mozilla.com dmitchell@mozilla.com

This will work retroactively, so there's no need to re-run `ccm-update` after merging users.
