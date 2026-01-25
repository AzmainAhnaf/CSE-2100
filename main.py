import requests
import random
import json

base_url = "https://codeforces.com/api/"

# get random active user from CF with rating >= lo and <= hi
# Max size of the returned list is limit 
def get_userbase(lo, hi, limit):
    url = base_url + "user.ratedList?activeOnly=true&includeRetired=false"
    response = requests.get(url)
    data = response.json()
    idx = 0
    users = list()
    universal = data["result"]
    random.shuffle(universal)
    for person in universal:
        rating = person["rating"]
        if rating >= lo and rating <= hi:
            users.append([person["handle"], rating])
        if (len(users) >= limit):
            break
    return users

# Print userbase (for debugging purposes)
def print_userbase(users):
    for user in users:
        print(user[0], user[1])

# Function to retrieve handle information from CF API
def get_user(handle):
    url = base_url + "user.info?handles=" + handle + "&checkHistoricHandles=true"
    response = requests.get(url)
    data = response.json()
    return data

# Check Max 'lmt' latest submission of the user 'handle'
# Return list of AC Submission of unique problems
def get_submissions(handle, lmt):
    url = base_url + "user.status?handle=" + handle + "&from=1&count=" + str(lmt)
    response = requests.get(url)
    data = response.json()
    already_exist = set()
    ndata = list()
    for item in data["result"]:
        if item["verdict"] == "OK" and item["id"] not in already_exist:
            already_exist.add(item['id'])
            ndata.append(item)
    return ndata

def get_all_submissions(handle, lmt):
    url = base_url + "user.status?handle=" + handle + "&from=1&count=" + str(lmt)
    response = requests.get(url)
    data = response.json()
    return data["result"]

def fetch_top_three_tag(item):
    tags = item["problem"]["tags"]
    if len(tags) < 3:
        return tags
    else:
        return tags[:3]


def main():
    # Taking input handle
    print("Input Handle: ", end="")
    handle = input()

    # Checking existence of User. If found fetching userbase around user's rating
    data = get_user(handle)

    # Stores relevant userbase
    users = list()

    # Stores rating of the user if found
    rating = 0
    if (data["status"] == "OK"):
        print("Handle Found")
        rating = data["result"][0]["rating"]
        print(f"Fetching Random Handles ranging [{rating - 100}, {rating + 100}]")
        users = get_userbase(rating - 100, rating + 100, 10)
    else:
        print(data["comment"])
        return -1

    print("Userbase fetched")

    # Getting submissions for each userbase and keeping track of count of each individual tag
    tc = 0
    tagcount = dict()
    for user in users:
        print(f"Processing {user[0]}, Rating: {user[1]}")
        submission = get_submissions(user[0], 10)
        for item in submission:
            for tag in fetch_top_three_tag(item):
                tc += 1
                if tag in tagcount:
                    tagcount[tag] += 1
                else:
                    tagcount[tag] = 1
    
    print("total tag count", tc)
    for key in tagcount:
        print(key, tagcount[key])
 
    count = 0 # Count of total considered submission
    total = dict() # Store count of total submission of a specific tag
    bad = dict()  # Store count of bad submission of a specific tag
    good = dict() # Store count of good submission of a specific tag

    submission = get_all_submissions(handle, 20)

    # Filtering out submission based on accepted, and wrong verdict
    submission_count = 0
    for item in submission:
        verdict = item["verdict"]
        print(item["id"], verdict)
        if verdict == "COMPILATION_ERROR":
            continue
        if "rating" not in item["problem"]:
            continue
        if verdict == "OK":
            if item["problem"]["rating"] < rating - 150:
                continue
            for tag in fetch_top_three_tag(item):
                print(tag)
                if tag in good:
                    good[tag] += 1
                else:
                    good[tag] = 1
                if tag in total:
                    total[tag] += 1
                else:
                    total[tag] = 1
                if tag not in bad:
                    bad[tag] = 0
        else:
            if item["problem"]["rating"] > rating + 200:
                continue
            for tag in fetch_top_three_tag(item):
                print(tag)
                if tag in bad:
                    bad[tag] += 1
                else:
                    bad[tag] = 1
                if tag in total:
                    total[tag] += 1
                else:
                    total[tag] = 1
                if tag not in good:
                    good[tag] = 0

    for key in total:
        print(f"{key} Total = {total[key]}, Good = {good[key]}, Bad = {bad[key]}")
    
    

if __name__ == "__main__":
    main()