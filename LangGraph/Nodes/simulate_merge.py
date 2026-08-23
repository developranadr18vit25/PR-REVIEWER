import os
import subprocess
import tempfile
import shutil

from workFlow import PR_State

def run_git(command, cwd):

    result = subprocess.run(
        command,
        cwd=cwd,
        capture_output=True,
        text=True
    )

    if result.returncode != 0:

        raise RuntimeError(
            f"""
Git command failed:

Command:
{' '.join(command)}

STDOUT:
{result.stdout}

STDERR:
{result.stderr}
"""
        )

    return result


def simulate_merge(state: PR_State):

    repo_path = state["repo_path"]

    pr_number = state["pr_number"]

    target_branch = state["target_branch"]

    temp_dir = tempfile.mkdtemp(
        prefix=f"pr-{pr_number}-"
    )

    worktree_created = False


    try:

        run_git(
            [
                "git",
                "fetch",
                "origin",
                f"pull/{pr_number}/head:pr-{pr_number}"
            ],
            repo_path
        )

        run_git(
            [
                "git",
                "worktree",
                "add",
                "--detach",
                temp_dir,
                target_branch
            ],
            repo_path
        )

        worktree_created = True

        merge_result = subprocess.run(
            [
                "git",
                "merge",
                f"pr-{pr_number}",

                "--no-commit",

                "--no-ff"
            ],

            cwd=temp_dir,

            capture_output=True,

            text=True
        )


        if merge_result.returncode != 0:


            conflict_result = subprocess.run(
                [
                    "git",
                    "diff",
                    "--name-only",
                    "--diff-filter=U"
                ],

                cwd=temp_dir,

                capture_output=True,

                text=True
            )


            conflicts = [

                line.strip()

                for line in conflict_result.stdout.splitlines()

                if line.strip()

            ]


            return {
                "simulated_merge": {

                    "success": False,

                    "merge_conflict": True,

                    "conflicting_files": conflicts,

                    "error": (
                        merge_result.stdout
                        + merge_result.stderr
                    ),

                    "worktree": temp_dir
                }
            }


        status_result = run_git(
            [
                "git",
                "status",
                "--short"
            ],

            temp_dir
        )

        diff_result = run_git(
            [
                "git",
                "diff",
                "--name-only",
                target_branch
            ],

            temp_dir
        )


        merged_files = [

            line.strip()

            for line in diff_result.stdout.splitlines()

            if line.strip()

        ]

        return {

            "simulated_merge": {

                "success": True,

                "merge_conflict": False,

                "worktree": temp_dir,

                "merged_files": merged_files,

                "status": status_result.stdout
            }
        }


    except Exception as e:

        if worktree_created:

            try:

                run_git(
                    [
                        "git",
                        "worktree",
                        "remove",
                        "--force",
                        temp_dir
                    ],

                    repo_path
                )

            except Exception:

                pass

        else:

            shutil.rmtree(
                temp_dir,
                ignore_errors=True
            )


        return {

            "simulated_merge": {

                "success": False,

                "merge_conflict": False,

                "error": str(e)
            }
        }