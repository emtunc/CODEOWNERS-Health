# CODEOWNERS Health

## What is this?
Whilst applying branch protection rules to all repositories, I noticed that `Require review from Code Owners` fails silently if the repository falls into one of the following easy-to-trip-over scenarios:

- The repository doesn't have a CODEOWNERS file
- The repository has a CODEOWNERS file but the teams defined in the file don't exist in the repository ACL

I can't answer the question as to why an administrative/security control fails silently with no warning, but I can say that I was annoyed enough to script something to try and catch the silent failures.

Running the script will output two files; one to show you repositories that do not have a CODEOWNERS file and the other will show you the repositories which do not have permissions set correctly.
The script will only run against repositories that are private and not archived.

## Prerequisites
- Python 3 (tested on 3.9.7 but I'm sure it'll work on older versions)
- The script assumes you're running against a GitHub org
- The script assumes your CODEOWNERS files uses references to Teams and not Users

## Usage
- Add a Personal Access Token (PAT) to an environment variable called `GITHUB_TOKEN`
- Add the Org name to an envionment variable called `GITHUB_ORG`
- `pip install -r requirements.txt`
- `python3 main.py`

## Contributions
My Python isn't the greatest so please contribute if you have some improvements to make!
