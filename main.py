import concurrent.futures
import os
import random
import re
import time

import github.GithubException
from github import Github

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_ORG = os.getenv("GITHUB_ORG")
REQUESTS_PER_SECOND_TO_ACHIEVE = 5  # we should avoid hammering the Github API
MAX_WORKERS = 1000  # network requests are already spaced out so we don't need to be aggressive here
CODEOWNERS_REGEX = fr"[a-zA-Z/*]*@{GITHUB_ORG}/([a-zA-Z-]*)"

repositories_with_no_codeowners_file = []
repositories_with_access_conflicts = []
g = Github(GITHUB_TOKEN)

if not GITHUB_ORG or not GITHUB_TOKEN:
    print(f"You must set environment variables for GITHUB_ORG and GITHUB_TOKEN")
    exit(1)


def get_list_of_repos():
    repositories = []
    for repository in g.get_organization(GITHUB_ORG).get_repos():
        if repository.private and not repository.archived:
            repositories.append(repository.name)
    return repositories


def check_for_codeowners_file(repository, max_seconds):
    try:
        time.sleep(random.uniform(0, max_seconds))
        repository_object = g.get_repo(f"{GITHUB_ORG}/{repository}")
        codeowners_content = repository_object.get_contents("CODEOWNERS")
        check_codeowners_existence_in_repo_acl(repository_object, codeowners_content)

    except github.UnknownObjectException:
        print(f"{repository} - CODEOWNERS not found")
        repositories_with_no_codeowners_file.append(repository)
    except github.RateLimitExceededException:
        print(f"Rate limit exceeded!")


def check_codeowners_existence_in_repo_acl(repository, codeowners_content):
    try:
        repository_access_list = []
        repository_acl = repository.get_teams()
        [repository_access_list.append(team.name) for team in repository_acl]
        teams_in_codeowners = set(re.findall(CODEOWNERS_REGEX, codeowners_content.decoded_content.decode()))
        for team in teams_in_codeowners:
            if team not in repository_access_list:
                team_object = get_team_object(team)
                if not team_object.parent:
                    print(f"{repository.name} has {team} in the CODEOWNERS file but that team doesn't have access!")
                    repositories_with_access_conflicts.append(f"{repository.name},{team}")
                elif team_object.parent:
                    nested_teams = [team]
                    current_iteration = team_object.parent.name
                    while True:
                        parent_team = get_team_object(current_iteration)
                        nested_teams.append(parent_team.name)
                        if parent_team.parent:
                            current_iteration = parent_team.parent.name
                        else:
                            break
                    if not any(x in nested_teams for x in repository_access_list):
                        print(f"{repository.name} has {team} in the CODEOWNERS file but that team doesn't have access!")
                        repositories_with_access_conflicts.append(f"{repository.name},{team}")

    except Exception as error:
        print(f"{error}")


def get_team_object(team_name):
    return g.get_organization(GITHUB_ORG).get_team_by_slug(team_name)


def write_results_to_output():
    if repositories_with_no_codeowners_file:
        with open("no_codeowners.txt", "a") as no_codeowners:
            for item in sorted(repositories_with_no_codeowners_file, key=str.lower):
                no_codeowners.write("%s\n" % item)
    if repositories_with_access_conflicts:
        with open("access_conflicts.txt", "a") as access_conflicts:
            for item in sorted(repositories_with_access_conflicts, key=str.lower):
                access_conflicts.write("%s\n" % item)


with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
    try:
        repos = get_list_of_repos()
        complete_within_seconds = len(repos) / REQUESTS_PER_SECOND_TO_ACHIEVE
        print(f"Checking {len(repos)} repositories. This will take approximately {complete_within_seconds} seconds")
        for repo in repos:
            executor.submit(check_for_codeowners_file, repo, complete_within_seconds)
    except github.RateLimitExceededException:
        print(f"Rate limit exceeded!")

write_results_to_output()
