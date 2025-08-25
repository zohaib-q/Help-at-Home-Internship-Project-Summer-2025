import requests
from actions import actions
import base64
import re

class changeYaml:
    def __init__(self, GITHUB_TOKEN):
        '''
        initializes the github token and the headers and the ruamel yaml configuration
        '''
        self.github_token = GITHUB_TOKEN
        if not GITHUB_TOKEN:
            raise EnvironmentError("GITHUB_TOKEN is not set. Please export it or set it in the environment.")
        self.headers = {
            "Authorization": f"Bearer {self.github_token}",
            "Accept": "application/vnd.github+json"
        }
        self.verify = True


    def get_workflow_files(self, owner, repo):
        '''
        Gets all of the yaml files in the repo
        Parameters:
            owner - the org behind the repo
            repo - the repo you want to scan for workflows

        Returns:
            A list Containing all of the yaml and yml files in the repo
        '''
        url = f"https://api.github.com/repos/{owner}/{repo}/contents/.github/workflows"
        r = requests.get(url, headers=self.headers, verify=self.verify)
        if r.status_code == 404:
            print(f"No workflows found in {owner}/{repo}")
            return []
        r.raise_for_status()
        content = r.json()
        return [item["path"] for item in content if item["name"].endswith((".yml", ".yaml"))]


    def get_file_content(self, owner, repo, path):
        '''
        Gets the content of the yaml files
        Parameters:
            owner - org behind the repo
            repo - repo with the yaml files
            path - rest of the file path to the specific yaml file you want to access

        Returns:
            The contents of a specific yaml file
        '''
        url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
        r = requests.get(url, headers = self.headers, verify=self.verify)
        r.raise_for_status()
        content = r.json()["content"]
        return base64.b64decode(content).decode()


    def replace(self, lines, sha_map):
        """
        Replaces GitHub Action `uses:` tags in YAML lines with pinned commit SHAs.

        Parameters:
            lines (list of str): The lines of a YAML file, typically from .splitlines(keepends=True)
            sha_map (dict): A mapping of action repos (e.g. 'actions/checkout') to commit SHAs

        Returns:
            list of str: Updated lines with pinned SHAs where applicable
        """
        updated_lines = []
        uses_pattern = re.compile(r'^(\s*uses:\s*)(\S+?)@([^\s#]+)(.*)$')
        for line in lines:
            #checks if the line we are on has uses: <org>/<repo>@<tag>
            match = uses_pattern.match(line)
            if match:
                #prefix = uses, repo = org/repo, tag = @tag, suffix = comments
                prefix, repo, tag, suffix = match.groups() 
                if repo in sha_map:
                    #changes the line so that it uses commit SHA and not tag
                    new_line = f"{prefix}{repo}@{sha_map[repo]}{suffix}\n"
                    print(f"Pinning {repo} from {tag} to {sha_map[repo]}")
                    updated_lines.append(new_line)
                    continue
            #if a line isnt updated put the original line back in its place
            updated_lines.append(line)
        return updated_lines
    
    def process_repo_workflow(self, owner, repo, sha_map):
        '''
        Goes through all of the yaml files in the repo and changes the tags to commit SHAs
        Parameters:
            owner - the org
            repo - the specific repo you are working on
            sha_map - The dataframe of all the trusted libraries and their commit shas
                      We see if the library is in the data frame and if it is we replace
                      the tag with the commit SHA from the sha_map
        Returns:
            The updated yaml file
        '''
        updates = []
        paths = self.get_workflow_files(owner, repo)
        for path in paths:
            try:
                #Gets the file content
                content = self.get_file_content(owner, repo, path)
                #use split lines to maintain original formatting
                original_lines = content.splitlines(keepends = True)
                #updates the file to use commit SHAs instead of tags
                updated_lines = self.replace(original_lines, sha_map)

                if original_lines != updated_lines:
                    updated_content = ''.join(updated_lines)
                    print(f"\nUpdated {owner}/{repo}/{path}")
                    updates.append((path, updated_content))
                    # print(updated_content)
                else:
                    print(f"\n No changes in {path}")
            except Exception as e:
                print(f"Error processing {owner}/{repo}/{path} : {e}")

        return updates