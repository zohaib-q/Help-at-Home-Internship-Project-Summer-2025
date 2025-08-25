# devops-common-services
A repo to hold tools used for devops purposes.
This code when run locally creates a PR to resolve the "Unpinned tag for a non-immutable Action in workflow" code scan vulnerability

7 verified libraries:
  1. hashicorp/setup-terraform
  2. terraform-docs/gh-actions
  3. aws-actions/configure-aws-credentials
  4. aws-actions/amazon-ecr-login
  5. stefanzweifel/git-auto-commit-action
  6. azure/login
  7. azure/webapps-deploy

This code goes into the YAML files of the selected repos and replaces the version tags with the commit SHAs of the latest version for each repo, applies those changes to a new branch named "unpinned-tag-fix" and submits a pull request with the updated code to each of the selected repos.

The .yaml file in this repo just runs an action to give you a table of the verified libraries and their latest version commit hash along with a link to verify.

To get code to fully work you must run the trusted-github-action-tags folder locally through merger.py
If you just want to see the table of the updated commit SHAs you can run the action

How to get code to work:
- In merger.py:
    - line 17: Enter which repos you want to update

- In gitActions.py:
    - line 103: input your github username
    - line 104: input your HAH email

- If the code doesn't run:
    - Go through each file and set self.verify to False
    - The tag of the library you are trying to replace may not be in actions.py; add it there then rerun
    - There may exist a branch with the same name. You can rename the branch at merger.py line 18
    - The github token expired so you need to make a new classic token with proper permissions and place it in systems manager parameter store
            - the token should have full repo and workflow scope
