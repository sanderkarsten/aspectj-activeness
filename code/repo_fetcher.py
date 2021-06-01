import json

from pydriller import RepositoryMining
from dateutil.relativedelta import relativedelta
import datetime
from resources.url_resource import URLResource
import progressbar
import dateutil.parser
import pytz
import csv
import re

resources = {
    "search_repo": URLResource("https://api.github.com/search/repositories", "search"),
}

aspectJ_query = "aspectj pushed:>=2016-01-01"
spring_aop_query = "spring aop pushed:>=2016-01-01"
aop_topic_query = "topic:aop pushed:>=2016-01-01"
java_query = "language:Java pushed:>=2016-01-01"
general_query = "pushed:>=2016-01-01"
haskell_query = "language:Haskell pushed:>=2016-01-01"
date_format = "%Y-%m"
start_date = datetime.date(2016, 1, 1)
utc = pytz.UTC


# This method is used to find out the number of repos for a given query
def fetch_number_of_repos(query):
    params = {"q": query}
    result = resources["search_repo"].get(params).json()
    print(f'The total count of active repos is: {result["total_count"]}')


# Fetch information about all repos and save to json file for a given query
def fetch_all_repos(query, out_file):
    params = {"q": query}
    result = resources["search_repo"].get_multiple_pages(params)
    with open(out_file, "w") as outfile:
        json.dump({'repos': result}, outfile)


# Retrieves the activeness for all repositories, this function performs the actual mining of commits and can take
# quite some time. The input file must be a result returned by fetch_all_repos.
def get_activeness_for_repos(out_file, in_file):
    with open(in_file) as file:
        json_repos = json.load(file)
    repos = json_repos["repos"]
    result = {"total_issues": 0,
              "total_forks": 0,
              "repos": []
              }
    bar = progressbar.ProgressBar(maxval=len(repos),
                                  widgets=[progressbar.Bar('=', '[', ']'), ' ',
                                           progressbar.SimpleProgress()]
                                  )
    bar.start()
    rc = 0
    for repo in repos:
        append_info = {
            "id": repo["id"],
            "name": repo["name"],
            "html_url": repo["html_url"],
            "url": repo["url"],
            "created_at": repo["created_at"],
            "updated_at": repo["updated_at"],
            "pushed_at": repo["pushed_at"],
            "open_issues": repo["open_issues"],
            "number_of_commits": 0,
            "commits": [],
            "forks": repo["forks"],
            "failed": False
        }

        try:
            for c in RepositoryMining(repo["html_url"]).traverse_commits():
                append_info["commits"].append({
                    "deletions": c.deletions,
                    "insertions": c.insertions,
                    "lines": c.lines,
                    "files": c.files,
                    "message": c.msg,
                    "date": c.committer_date.isoformat().format()
                })
                append_info["number_of_commits"] = append_info["number_of_commits"] + 1
            result["total_issues"] += repo["open_issues"]
            result["total_forks"] += repo["forks"]
        except Exception:
            append_info["failed"] = True

        result["repos"].append(append_info)
        rc = rc + 1
        bar.update(rc)

    with open(out_file, "w") as outfile:
        json.dump({'repos': result}, outfile)


# This function writes the activeness to a csv file for a given activeness json file created by get_activeness_for_repos
def plot_activeness(out_file, in_file):
    with open(in_file) as file:
        repos = json.load(file)["repos"]["repos"]
    commit_info = create_month_range({
        "insertions": 0,
        "deletions": 0,
        "number_of_commits": 0,
        "files": 0,
        "lines": 0
    })
    for repo in repos:
        for commit in repo["commits"]:
            date = dateutil.parser.isoparse(commit["date"])
            if date >= utc.localize(datetime.datetime.combine(start_date, datetime.datetime.min.time())):
                key = date.strftime(date_format)
                commit_info[key]["insertions"] += commit["insertions"]
                commit_info[key]["deletions"] += commit["deletions"]
                commit_info[key]["number_of_commits"] += 1
                commit_info[key]["files"] += commit["files"]
                commit_info[key]["lines"] += commit["lines"]
    csv_columns = ["date", "insertions", "deletions", "number_of_commits", "files", "lines"]
    with open(out_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=csv_columns)
        writer.writeheader()
        for date, info in commit_info.items():
            info["date"] = date
            writer.writerow(info)


# This function prints the amount of issues per month to a csv file
def plot_issues(out_file, in_file):
    with open(in_file) as file:
        issues = json.load(file)["issues"]
    issue_info = create_month_range({"created": 0, "updated": 0})
    for issue in issues:

        c_date = dateutil.parser.isoparse(issue["created_at"])
        key_c = c_date.strftime(date_format)
        u_date = dateutil.parser.isoparse(issue["updated_at"])
        key_u = u_date.strftime(date_format)

        if datetime.date(2016, 1, 1) <= c_date.date():
            issue_info[key_c]["created"] += 1
        if datetime.date(2016, 1, 1) <= u_date.date():
            issue_info[key_u]["updated"] += 1
    csv_columns = ["date", "created", "updated"]
    with open(out_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=csv_columns)
        writer.writeheader()
        for date, info in issue_info.items():
            info["date"] = date
            writer.writerow(info)


# Helper function to create a month range of the period used in the research
def create_month_range(content):
    result = {}
    current = datetime.date(2016, 1, 1)
    today = datetime.date.today()
    while current <= today:
        result[current.strftime(date_format)] = content.copy()
        current += relativedelta(months=1)
    return result


# This function retrieves all issues for the repositories in a given file, these are returned by
# get_activeness_for_repos
def get_issues(out_file, in_file):
    with open(in_file) as file:
        json_repos = json.load(file)
        repos = json_repos["repos"]
        issues = []
        for repo in repos:
            if repo["open_issues_count"] > 0:
                url = repo["issues_url"].replace('{/number}', '')
                response = URLResource(url, "core").get().json()
                issues = issues + response
    with open(out_file, "w") as outfile:
        json.dump({'issues': issues}, outfile)


# This function returns topics based on a given search query and writes these to a file
def get_topics(query, out_file):
    params = {"q": query}
    labels = {}
    result = resources["search_repo"].get_multiple_pages(params)
    for repo in result:
        topics = repo["topics"]
        for name in topics:
            if name in labels:
                labels[name] += 1
            else:
                labels[name] = 0
    with open(out_file, 'w') as f:
        for key in labels.keys():
            f.write("%s,%s\n" % (key, labels[key]))


# Prints all mentions from an issue file returned by get_issues, and an activeness file returned by
# get_activeness_for_repos. Mentions can be fetched based on a given list of patterns
def get_mentions(activeness_file_name, issue_file_name, patterns):
    with open(activeness_file_name) as a_file:
        repos = json.load(a_file)["repos"]["repos"]
    with open(issue_file_name) as i_file:
        issues = json.load(i_file)["issues"]
    count = 0
    for repo in repos:
        for commit in repo["commits"]:
            message = commit["message"]
            should_print = False
            for pattern in patterns:
                if re.search(pattern, message, re.IGNORECASE):
                    should_print = True
            if should_print:
                count = count + 1
                print("\n======================= Commit (" + str(count) + ") =================================")
                print(message)
                print(repo["html_url"])
                print(commit["date"])
    count = 0
    for issue in issues:
        message = issue["body"]
        should_print = False
        for pattern in patterns:
            if re.search(pattern, message, re.IGNORECASE):
                should_print = True
        if should_print:
            count = count + 1
            print("\n======================= Issue (" + str(count) + ") =================================")
            print(message)
            print(issue["html_url"])


if __name__ == '__main__':
    print("please call one of the operations in the main function")

    # Examples of how the functions can be called:
    # fetch_number_of_repos("aspectj")
    # fetch_number_of_repos(spring_aop_query)
    #
    # fetch_all_repos(spring_aop_query, "spring_repos.json")
    #
    # get_activeness_for_repos("activeness/aspectj_activeness.json", "activeness/aspectJ_repos.json")
    #
    # get_mentions("activeness/aspectj_activeness.json", "activeness/issues_AspectJ.json",
    #              ["spring aop", "springaop", "aop spring"])
    #
    # get_topics(aop_topic_query)
    #
    # plot_issues("activeness/issues_spring_total.csv", "activeness/issues_spring_aop.json")
