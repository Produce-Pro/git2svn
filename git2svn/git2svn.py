import os
import sys
import time
from typing import Dict, Optional

import git
import svn.local
import typer

app = typer.Typer()


def main(
    DIR: str = typer.Option(os.getcwd(), help="Git & SVN Working Directory"),
    START_REV: Optional[str] = typer.Option("", help="Starting Git commit revision"),
):
    if not os.path.isdir(DIR):
        typer.echo("Invalid directory", err=True)
        return 1
    else:
        typer.echo(f"Directory: {DIR}")

    svn_repo = svn.local.LocalClient(DIR)
    try:
        typer.echo("SVN repo found\n", svn_repo.info()["repository/root"])
    except svn.exception.SvnException:
        typer.echo("Invalid svn repository", err=True)
        return 1

    try:
        git_repo = git.Repo(DIR)
    except git.exc.InvalidGitRepositoryError:
        typer.echo("Invalid git repository", err=True)
        return 1

    if git_repo.bare:
        typer.echo("Empty git repository", err=True)
        return 1

    typer.echo("GIT repo found")
    if not typer.confirm("Are you sure you want to continue?"):
        return 1

    # Make sure we are back at master
    git_repo.git.checkout("master", "--force")

    # Use manually command to get every log hash
    git_log = git_repo.git.log("--pretty=%H").split("\n")

    typer.echo(
        f"  Last commit {typer.echo(time.asctime(time.gmtime(git_repo.head.commit.committed_date)))}"
    )
    typer.echo(f"  Entries {len(git_log)}")

    if START_REV != "":
        typer.echo("Starting revision:")
        typer.echo(START_REV)

    rev = svn_repo.info()["commit_revision"]

    svn_commit_count = 0
    svn_count: Dict = dict()

    count = dict()
    count["total"] = len(git_log)
    count["current"] = -1
    # Commit each git commit into svn
    for ch in git_log[::-1]:
        count["current"] += 1
        if START_REV != "" and not ch.startswith(START_REV):
            continue
        else:
            START_REV = ""
        typer.echo("-----------------------------------------------------")
        typer.echo(f'{count["current"]}/{count["total"]}')
        commit = git_repo.commit(ch)
        commit_date = time.asctime(time.gmtime(commit.committed_date))
        typer.echo(f"{commit_date} {commit}")
        typer.echo(commit.message)
        git_repo.git.checkout(ch, "--force")

        # if not ask_continue():
        #     return 1

        try:
            svn_count.clear()
            svn_status = svn_repo.status()

            for fs in svn_status:
                if fs.name.find(".git/") != -1:
                    typer.echo(f"Git repository is being included in svn {fs.name}")
                    raise Exception
                status = fs.type_raw_name
                if status in svn_count:
                    svn_count[status] += 1
                else:
                    svn_count[status] = 1
                if status in ["unversioned"]:
                    # typer.echo('add',fs.name)
                    svn_repo.add(fs.name)
                elif status in ["missing"]:
                    # typer.echo('remove',fs.name)
                    svn_repo.run_command("remove", [fs.name])
                elif status in ["modified", "added", "normal", "deleted"]:
                    continue
                else:
                    typer.echo(f"Unknown status: {status}")
                    raise Exception

        except:
            typer.echo("SVN add/remove error:")
            typer.echo(sys.exc_info()[0])
            typer.echo(status)
            typer.echo(fs.name)
            return 1

        typer.echo(f"SVN Changes:\n {svn_count}")

        if commit.message.startswith("gits"):
            message = commit.message
        else:
            message = commit.committer.name + " " + commit_date + "\n" + commit.message

        try:
            svn_repo.commit(message)
            svn_repo.update()
            if rev >= svn_repo.info()["commit_revision"]:
                typer.echo("SVN commit failed: Nothing committed")
                continue

            rev = svn_repo.info()["commit_revision"]

            typer.echo("SVN revision: ", svn_repo.info()["commit_revision"])
            svn_commit_count += 1
        except:
            typer.echo(f"SVN commit failed: {sys.exc_info()[0]}")
            return 1

        typer.echo("")

    typer.echo("SVN Commits:\n {svn_commit_count}")
    return 0


def cli():
    typer.run(main)


if __name__ == "__main__":
    cli()

