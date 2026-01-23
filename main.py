import requests
import random
import json

base_url = "https://codeforces.com/api/"

# get random active user from CF with rating >= lo and <= hi
# Max size of the returned list is limit 
def get_userbase(lo, hi, limit):
    url = base_url + "user.ratedList?activeOnly=true&includeRetired=false"
    response = requests.get(url)
    response.raise_for_status()

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

# Fetch Max 'lmt' latest submission of the user 'handle'
def get_submissions(handle, lmt):
    url = base_url + "user.status?handle=" + handle + "&from=1&count=" + str(lmt)
    response = requests.get(url)
    data = response.json()
    return data

def main():
    # Taking input handle
    print("Input Handle: ", end="")
    handle = input()

    # Checking existence of User. If found fetching userbase around user's rating
    data = get_user(handle)
    users = list()
    if (data["status"] == "OK"):
        print("Handle Found")
        print("Random Handles ranging around the inputted handles")
        rating = data["result"][0]["rating"]
        users = get_userbase(rating - 100, rating + 100, 10)
    else:
        print(data["comment"])
        return -1
    
    print("Userbase fetched")
    print_userbase(users)

    submission = get_submissions()
    
    # Filtering out problemId
    # pid = list()
    # for user in users:
    #     name = user[0]
    #     name_pid = set()
    #     name_submissions = get_submissions(name, 10)
    #     for submission in name_submissions["result"]:
    #         name_pid.add(submission['id'])
    #     pid.append(name_pid)

    # for problems in pid:
    #     for problem in problems:
    #         print(problem, end=" ")
    #     print()

if __name__ == "__main__":
    main()