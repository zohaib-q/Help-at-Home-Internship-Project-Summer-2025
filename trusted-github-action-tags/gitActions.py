import requests
import base64

class GitHubPR:
    def __init__(self, GITHUB_TOKEN):
        '''
        initializes the headers with the personal access token
        '''
        self.headers = {
            "Authorization": f"Bearer {GITHUB_TOKEN}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28"
        }
        self.verify = True
    
    def get_default_branch(self, owner, repo):
        '''
        gets the default branch of the repo it is checking
        Parameters:
            owner - the org
            repo - the repo you are checking
        Returns:
            The default branch of the repo
        '''
        url = f"https://api.github.com/repos/{owner}/{repo}"
        r = requests.get(url, headers=self.headers, verify = self.verify)
        r.raise_for_status()
        return r.json()["default_branch"]
    
    def get_latest_commit(self, owner, repo, branch):
        '''
        Gets the latest commit of the default branch of the repo
        Parameters:
            owner - the org
            repo - The repo you are checking
            branch - the default branch of the repo
        Returns:
            The latest commit SHA of the default branch of the repo
        '''
        url = f"https://api.github.com/repos/{owner}/{repo}/git/ref/heads/{branch}"
        r = requests.get(url, headers=self.headers, verify=self.verify)
        r.raise_for_status()
        return r.json()["object"]["sha"]

    def make_branch(self, owner, repo, new_branch, sha):
        '''
        Makes a new branch from the latest commit of the default branch
        Parameters:
            owner - the org
            repo - the repo you are checking
            new_branch - The name of the new branch you would like to create
            sha - The latest commit SHA of the default branch
        Returns:
            the json of the post request made to create the new branch
        '''
        url = f"https://api.github.com/repos/{owner}/{repo}/git/refs"
        data = {
            "ref" : f"refs/heads/{new_branch}",
            "sha" : sha
        }
        r = requests.post(url, headers=self.headers, json = data, verify=self.verify)
        r.raise_for_status()
        print(f"New Branch: {new_branch}")
        return r.json()
    
    def get_sha(self, owner, repo, path, branch):
        '''
        Gets the latest commit SHA of the new branch
        Parameters:
            owner - the org
            repo - the repo you are checking
            path - Path to get to the root of the repo
            branch - the new branch name
        Returns:
            the latest commit SHA
        '''
        url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}?ref={branch}"
        r = requests.get(url, headers=self.headers, verify = self.verify)
        r.raise_for_status()
        return r.json()["sha"]
    
    def update_file(self, owner, repo, path, branch, new_content_str, sha, commit_message):
        '''
        makes the changes to the yaml file with the updated yaml content from the editYaml file
        Parameters:
            owner - the org
            repo - the repo you are on currently
            path - the rest of the path to the yaml file
            branch - The new branch you made that you will be committing to
            new_content_str - the new content of the yaml file that you are replacing the original content with
            sha - the latest commit SHA of the new branch
        Returns:
            the json from the put request to commmit the updated yaml content
            or if it fails, the error details
        '''
        print(new_content_str)
        url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
        encodedContent = base64.b64encode(new_content_str.encode()).decode()
        
        #need this extra info to ensure you have access and to make the commit
        data = {
            "message" : commit_message,
            "committer" : 
                {"name" : "USERNAME",
                "email" : "EMAIL"},
            "content" : encodedContent,
            "branch" : branch,
            "sha" : sha,

        }
        try:
            r = requests.put(url, headers=self.headers, json = data, verify = self.verify)
            r.raise_for_status()
            print("file updated")
            return r.json()
        except requests.exceptions.HTTPError as e:
            print(f"Failed to update file.\nStatus Code: {r.status_code}\nResponse Body: {r.text}")
            raise e
    
    def createPR(self, owner, repo, mainBranch, branch, title, body = ""):
        '''
        Makes the pull request from the new branch to main
        Parameters:
            owner - the org
            repo - the repo you are on currently
            mainBranch - the default branch
            branch - the branch you updated
            title - the title of the pull request. Typically unpinned-tag-fix
            body - the body text of the pull request. left blank
        Returns:
            The json from the post request to make the pull request or if it fails,
            the error details
        '''
        url = f"https://api.github.com/repos/{owner}/{repo}/pulls"
        data = {
            "title" : title,
            "head": branch,
            "base": mainBranch,
            "body": body
        }
        try:
            r = requests.post(url, headers=self.headers, json = data, verify = self.verify)
            r.raise_for_status()
            print("Pull Request made")
            return r.json()
        except requests.exceptions.HTTPError as e:
            print(f"Failed to PR file.\nStatus Code: {r.status_code}\nResponse Body: {r.text}")
            raise e
        