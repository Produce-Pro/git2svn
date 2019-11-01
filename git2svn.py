
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
        'rev=',
    ],
    'short': 'hd:r:',
}

def ask_continue():
    try:
        input('Press Enter to continue...')
        return True
    except KeyboardInterrupt:
        print('\nAborted.')
        return False


def usage():
    print('git2svn: Commit git changes to svn')

def main():
    try:
        opts, args = getopt.getopt(sys.argv[1:],ARGS['short'],ARGS['long'])
    except getopt.GetoptError as err:
        usage()
        print(err)
        return 1

    START_REV=''
    DIR = os.getcwd()
    for o, a in opts:
        if o in ('-h', '--help'):
            usage()
            return 0
        elif o in ('-d', '--dir'):
            DIR=a
        elif o in ('-r', '--rev'):
            START_REV=a
        
    if not os.path.isdir(DIR):
        print('Invalid directory')
        return 1
    else:
        print('Directory:',DIR)
    try:
        git_repo = git.Repo(DIR)

    except git.exc.InvalidGitRepositoryError:
        print('Invalid git repository')
        return 1

    if git_repo.bare:
        print('Empty git repository')
        return 1

    # Make sure we are back at master
    git_repo.git.checkout('master','--force')


    # Use manually command to get every log hash
    git_log = git_repo.git.log('--pretty=%H').split('\n')

    print(
        'GIT repo found\n',
        'Last commit',time.asctime(time.gmtime(git_repo.head.commit.committed_date)),'\n',
        'Entries',len(git_log)
    )

    if START_REV != '':
        print('Starting revision:\n',START_REV)

    svn_repo = svn.local.LocalClient(DIR)
    try:
        print('SVN repo found\n',svn_repo.info()['repository/root'])
    except svn.exception.SvnException:
        print('Invalid svn repository')
        return 1

    if not ask_continue():
        return 1

    rev = svn_repo.info()['commit_revision']

    svn_commit_count=0
    svn_count = dict()

    count = dict()
    count['total'] = len(git_log)
    count['current'] = -1
    # Commit each git commit into svn
    for ch in git_log[::-1]:
        count['current']+=1
        if START_REV != '' and not ch.startswith(START_REV):
            continue
        else:
            START_REV=''
        print('-----------------------------------------------------')
        print(count['current'],'/',count['total'])
        commit = git_repo.commit(ch)
        commit_date=time.asctime(time.gmtime(commit.committed_date))
        print(commit_date,' ',commit)
        print(commit.message)
        git_repo.git.checkout(ch,'--force')

        
        # if not ask_continue():
        #     return 1

        try:
            svn_count.clear()
            svn_status = svn_repo.status()

            for fs in svn_status:
                if fs.name.find('.git/') != -1:
                    print('Git repository is being included in svn\n',fs.name)
                    raise Exception
                status = fs.type_raw_name
                if status in svn_count:
                    svn_count[status]+=1
                else:
                    svn_count[status]=1
                if status in [ 'unversioned' ]:
                    # print('add',fs.name)
                    svn_repo.add(fs.name)
                elif status in [ 'missing' ]:
                    # print('remove',fs.name)
                    svn_repo.run_command('remove',[fs.name])
                elif status in [ 'modified', 'added', 'normal', 'deleted' ]:
                    continue
                else:
                    print('Unknown status:',status)
                    raise Exception

        except:
            print(
                'SVN add/remove error:',
                '\n',sys.exc_info()[0],
                '\n',status,
                '\n',fs.name
            )
            return 1

        print("SVN Changes:\n",svn_count)

        if commit.message.startswith('gits'):
            message = commit.message
        else:
            message = commit.committer.name + ' ' + commit_date + '\n' + commit.message


        try:
            svn_repo.commit(message)
            svn_repo.update()
            if rev >= svn_repo.info()['commit_revision']:
                print('SVN commit failed: Nothing committed')
                continue

            rev = svn_repo.info()['commit_revision']

            print('SVN revision: ',svn_repo.info()['commit_revision'])
            svn_commit_count+=1
        except:
            print('SVN commit failed:',sys.exc_info()[0])
            return 1
        
        print('')


    print("SVN Commits:\n",svn_commit_count)
    return 0

main()
