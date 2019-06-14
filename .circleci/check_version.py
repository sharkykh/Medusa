# coding: utf-8
"""Check Medusa app version before release."""
import os
import re
import subprocess
import sys
from pathlib import Path

VERSION_FILE = 'medusa/common.py'
VERSION_LINE_REGEXP = re.compile(r"VERSION = '((?:\d+\.?)+)'")
CIRCLE = os.environ.get('CIRCLE', False)

if CIRCLE:
    CIRCLE_PULL_REQUEST = os.environ['CIRCLE_PULL_REQUEST']  # empty if not a PR, otherwise - the PR URL
    CIRCLE_PR_TARGET_BRANCH = None
    CIRCLE_PR_SOURCE_BRANCH = os.environ['CIRCLE_BRANCH']  # always the source branch
    CIRCLE_WORKING_DIRECTORY = Path(os.environ['CIRCLE_WORKING_DIRECTORY'])
else:
    CIRCLE_PULL_REQUEST = 'https://github.com/pymedusa/Medusa/pull/1234'
    CIRCLE_PR_TARGET_BRANCH = 'master'
    CIRCLE_PR_SOURCE_BRANCH = 'develop'  # or 'release/release-0.2.3'
    CIRCLE_WORKING_DIRECTORY = Path(__file__).parent.parent

if CIRCLE_PULL_REQUEST and CIRCLE_PR_TARGET_BRANCH is None:
    output = subprocess.check_output(
        ['git', 'merge-base', 'origin/develop', 'origin/master', CIRCLE_PR_SOURCE_BRANCH],
        universal_newlines=True,
    )
    merge_base_commit = output.strip()
    if not merge_base_commit:
        raise ValueError('merge_base_commit value is empty')

    output = subprocess.check_output(
        ['git', 'branch', merge_base_commit],
        universal_newlines=True,
    )
    CIRCLE_PR_TARGET_BRANCH = output.strip()
    if not CIRCLE_PR_TARGET_BRANCH:
        raise ValueError('CIRCLE_PR_TARGET_BRANCH value is empty')

CIRCLE_PR_TARGET_BRANCH = CIRCLE_PR_TARGET_BRANCH.lower()
CIRCLE_PR_SOURCE_BRANCH = CIRCLE_PR_SOURCE_BRANCH.lower()
CIRCLE_WORKING_DIRECTORY = CIRCLE_WORKING_DIRECTORY.absolute()


class Version(object):
    def __init__(self, version_string):
        self.version = tuple()
        if version_string.startswith('v'):
            version_string = version_string[1:]
        self.version = tuple(map(int, version_string.split('.')))

    def __eq__(self, other):
        return self.version == other.version

    def __ne__(self, other):
        return self.version != other.version

    def __lt__(self, other):
        return self.version < other.version

    def __le__(self, other):
        return self.version <= other.version

    def __gt__(self, other):
        return self.version > other.version

    def __ge__(self, other):
        return self.version >= other.version

    def __str__(self):
        return str('.'.join(map(str, self.version)))

    def __repr__(self):
        return repr(self.version)


def search_file_for_version():
    """Get the app version from the code."""
    version_file_path = CIRCLE_WORKING_DIRECTORY / VERSION_FILE
    with version_file_path.open('r', encoding='utf-8') as fh:
        for line in fh:
            match = VERSION_LINE_REGEXP.match(line)
            if match:
                return Version(match.group(1))

    raise ValueError('Failed to get the app version!')


# Are we merging either develop or a release branch into master in a pull request?
if all((
        CIRCLE_PULL_REQUEST,
        CIRCLE_PR_TARGET_BRANCH == 'master',
        CIRCLE_PR_SOURCE_BRANCH == 'develop' or CIRCLE_PR_SOURCE_BRANCH.startswith('release/')
)):
    # Get lastest git tag on master branch
    subprocess.check_call(['git', 'fetch', 'origin', 'master:master'])

    output = subprocess.check_output(
        ['git', 'describe', '--tags', '--abbrev=0', 'master'],
        universal_newlines=True,
    )
    latest_tag = output.strip()
    if not latest_tag:
        raise ValueError('Latest tag commit hash is empty')

    git_version = Version(latest_tag)
    file_version = search_file_for_version()
    print(f'GIT Version: {git_version}')
    print(f'APP Version: {file_version}')
    version_compare = file_version > git_version
    if not version_compare:
        print(f'Please update app version in {VERSION_FILE}')
        sys.exit(1)

# If we got here, then everything is correct!
sys.exit(0)
