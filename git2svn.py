
import svn.local
import git
import time
import os
import sys
import getopt

ARGS = {
    'long': [
        'help',
        'dir=',
    ],
    'short': 'hd:',
}


def usage():
    print('git2svn: Commit git changes to svn')

def main():
    try:
        opts, args = getopt.getopt(sys.argv[1:],ARGS['short'],ARGS['long'])
    except getopt.GetoptError as err:
        usage()
        print(err)
        return 1

    DIR = '/home/tcn_ppro/workspace/ppro-bash'
    for o, a in opts:
        if o in ('-h', '--help'):
            usage()
            return 0
        elif o in ('-d', '--dir'):
            DIR=a
        
    if not os.path.isdir(DIR):
        print('Invalid directory')
        return 1
    try:
        git_repo = git.Repo(DIR)

    except git.exc.InvalidGitRepositoryError:
        print('Invalid git repository')
        return 1

    if git_repo.bare:
        print('Empty git repository')
        return 1

    git_log = git_repo.head.log()
    if len(git_log) == 0:
        print('Git log empty')
        return 1

    print('Git log found:',len(git_log), 'entries')

    svn_repo = svn.local.LocalClient(DIR)
    try:
        print(svn_repo.info())
    except svn.exception.SvnException:
        print('Invalid svn repository')
        return 1

    try:
        input('Press Enter to continue...')
    except KeyboardInterrupt:
        print('\nAborted.')
        return 1



    # Commit each git commit into svn
    for cl in git_log:
        commit = git_repo.commit(cl.newhexsha)
        print(time.asctime(time.gmtime(commit.committed_date)),' ',commit)
        print(commit.message)

    return 0

    # git_repo.head.set_commit(commit)

main()
