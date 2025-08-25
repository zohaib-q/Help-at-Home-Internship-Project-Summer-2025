from editYaml import changeYaml
from getLatestHash import tagToSHA
from gitActions import GitHubPR
from actions import actions
import boto3
import botocore.exceptions
import os

def fetch_parameter(name, with_decryption=True):
    session = boto3.Session(profile_name="AWS_PROFILE_NAME")
    ssm = session.client('ssm', region_name = 'REGION')
    try:
        response = ssm.get_parameter(Name = name, WithDecryption = with_decryption)
        return response['Parameter']['Value']
    except botocore.exceptions.ClientError as error:
        print(f"ClientError: {error}")
        raise
    except Exception as e:
        print(f"Unexpected Error: {e}")
        raise


GITHUB_TOKEN = fetch_parameter('PATH_TO_TOKEN')

def main():
    '''
    Brings together all of the files
    Makes an updated data frame of the libraries, their version, and its commit SHA
    Updates the yaml files in the repos you want to fix by replacing the tags with commit SHAs
    Makes a branch in the repo with these changes
    Creates a Pull Request
    '''
    owner = "ORG"
    repos = ["REPOS_GO_HERE"]
    new_branch_name = "action_security_patch"

    #for building the table
    commitSHA = tagToSHA()
    df = commitSHA.form_table()
    sha_map = commitSHA.build_sha_map(df)

    #goes through all the repos in the list
    for repo in repos:
        #changes tags to commit SHAs in yaml files
        yaml_changer = changeYaml(GITHUB_TOKEN)
        updates = yaml_changer.process_repo_workflow(owner, repo, sha_map)

        if not updates:
            continue
        
        #makes new github branch
        githubBranch = GitHubPR(GITHUB_TOKEN)
        default = githubBranch.get_default_branch(owner, repo)
        default_commit = githubBranch.get_latest_commit(owner, repo, default)
        branch = githubBranch.make_branch(owner, repo, new_branch_name, default_commit)
        print(branch)
        
        #updates the file in the branch with the new content
        for path, content in updates:
            file_sha = githubBranch.get_sha(owner, repo, path, new_branch_name)
            githubBranch.update_file(owner, repo, path, new_branch_name, content, file_sha, "automated test")

        #makes a PR
        githubBranch.createPR(owner, repo, default, new_branch_name, "unpinned-tag-fix")


if __name__ == "__main__":
    main()