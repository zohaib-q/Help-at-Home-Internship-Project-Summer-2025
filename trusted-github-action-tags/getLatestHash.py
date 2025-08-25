import requests
from actions import actions
import pandas as pd
import os

class tagToSHA:
    def __init__(self):
        '''
        initializes the headers
        '''
        # self.headers = {
        #     "Accept": "application/vnd.github+json",
        #     "X-GitHub-Api-Version": "2022-11-28"
        # }
        # self.verify = True
        token = os.getenv("GITHUB_TOKEN")  # GitHub Actions sets this automatically
        self.headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "Authorization": f"Bearer {token}" if token else None
        }
        # remove None values if token not found
        self.headers = {k: v for k, v in self.headers.items() if v is not None}
        self.verify = True

    def get_latest_release_tag(self, owner, repo):
        '''
        Gets the latest version number of the repo
        Parameters:
            owner - the org that the repo is in
            repo - the actual tool that we are using

        Returns: 
            The latest version number of the repo
        '''
        url = f"https://api.github.com/repos/{owner}/{repo}/releases/latest"
        resp = requests.get(url, headers=self.headers, verify=self.verify)
        resp.raise_for_status()
        return resp.json()["tag_name"]


    def get_commit_sha(self, owner, repo):
        '''
        Gets the commit sha of the latest version of the repo
        Parameters:
            owner - the org that the repo is in
            repo - the actual tool we are using
            tag - the latest version number
        
        Returns:
            The 40 character commit SHA of the latest version
        '''
        tag = self.get_latest_release_tag(owner, repo)
        url_ref = f"https://api.github.com/repos/{owner}/{repo}/git/refs/tags/{tag}"
        r = requests.get(url_ref, headers=self.headers, verify=self.verify)
        r.raise_for_status()
        data_ref = r.json()
        #only first entry is relevant if list
        if isinstance(data_ref, list):
            data_ref = data_ref[0]
        obj = data_ref["object"]
        if obj["type"] == "commit":
            #lightweight tag - points to commit
            return obj["sha"]
        elif obj["type"] == "tag":
            #annotated tag - points to tag object then commit
            ting2 = requests.get(obj["url"], headers=self.headers, verify=self.verify)
            ting2.raise_for_status()
            data_tag = ting2.json()
            return data_tag["object"]["sha"]
        else:
            raise ValueError(f"Unexpected object type: {obj['type']}")


    def form_table(self):
        '''
        Makes a table with each row containing:
        org/rep         latest version          commit SHA          Link

        Returns:
            Dataframe containing the table
        '''
        rows = []
        for action in actions:
            #isolates owner and repo
            owner, repo = action.split("/")
            try:
                #gets all necessary information to construct table
                tag = self.get_latest_release_tag(owner, repo)
                sha = self.get_commit_sha(owner, repo)
                url = f"https://github.com/{owner}/{repo}/commit/{sha}"
                rows.append({
                    "Library" : f"{owner}/{repo}",
                    "Version" : tag,
                    "Commit SHA" : sha,
                    "Link" : url
                })
            except requests.HTTPError as e:
                print(f"[ERROR] {owner}/{repo}: {e.response.status_code} - {e.response.text}")
            except Exception as e:
                print(f"[ERROR] {owner}/{repo}: {e}")
            
        df = pd.DataFrame(rows)
        print(df.to_string(index = False))
        return df


    def build_sha_map(self, df):
        '''
        Makes dictionary of repo and commit SHA from the dataframe
        Parameters:
            df - the table dataframe that contains org/repo, version, commit SHA, link

        Returns:
            Dictionary containing Repo and Commit SHA
        '''
        return dict(zip(df["Library"], df["Commit SHA"]))


if __name__ == "__main__":
    '''
    Here so the YAML file outputs to actions the updated table on each run
    '''
    df = tagToSHA()
    print(df.form_table())

