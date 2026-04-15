import requests
import random

base_url = "https://codeforces.com/api/"

def get_userbase(lo, hi, limit):
    url = base_url + "user.ratedList?activeOnly=true&includeRetired=false"
    response = requests.get(url)
    data = response.json()
    users = list()
    universal = data["result"]

    # Binary Search for the lower bound
    l = 0
    r = len(universal) - 1
    while (l < r - 1):
        mid = (l + r) // 2
        if universal[mid]['rating'] < lo:
            r = mid
        else:
            l = mid
    right = l

    # Binary Search for the upper bound
    l = 0
    r = len(universal) - 1
    while (l < r - 1):
        mid = (l + r) // 2
        if universal[mid]['rating'] > hi:
            l = mid
        else:
            r = mid
    left = r

    # print(left, right)

    universal = universal[left:right+1]
    random.shuffle(universal)
    for person in universal:
        rating = person["rating"]
        if rating >= lo and rating <= hi:
            users.append([person["handle"], rating])
        if len(users) >= limit:
            break
    return users

def get_user(handle):
    url = base_url + "user.info?handles=" + handle + "&checkHistoricHandles=true"
    response = requests.get(url)
    data = response.json()
    return data

def get_submissions(handle, lmt):
    url = base_url + "user.status?handle=" + handle + "&from=1&count=" + str(lmt)
    response = requests.get(url)
    data = response.json()
    already_exist = set()
    ndata = list()
    for item in data["result"]:
        if item["verdict"] == "OK" and item["problem"]["name"] not in already_exist:
            already_exist.add(item['problem']["name"])
            ndata.append(item)
    return ndata

def get_all_submissions(handle, lmt):
    url = base_url + "user.status?handle=" + handle + "&from=1&count=" + str(lmt)
    response = requests.get(url)
    data = response.json()
    ndata = list()
    already_exist_good = set()
    already_exist_bad = set()
    for item in data["result"]:
        if item["verdict"] == "COMPILATION_ERROR":
            continue
        if item["verdict"] == "OK" and item["problem"]["name"] not in already_exist_good:
            already_exist_good.add(item["problem"]["name"])
            ndata.append(item)
        if item["verdict"] != "OK" and item["problem"]["name"] not in already_exist_bad:
            already_exist_bad.add(item["problem"]["name"])
            ndata.append(item)
    return ndata

def get_total_good_bad_submission(handle, lmt):
    data = get_user(handle)
    try:
        rating = data["result"][0]["rating"]
    except:
        rating = 0
    submission = get_all_submissions(handle, lmt)

    total = dict()
    bad = dict()
    good = dict()

    # Range analysis
    delta = (4000 - rating) // 12
    lo = max(800, rating - delta)
    hi = max(1000, rating + 2 * delta)

    for item in submission:
        verdict = item["verdict"]
        if "rating" not in item["problem"]:
            continue
        prob_rating = item["problem"]["rating"]
        if verdict == "COMPILATION_ERROR":
            continue
        if verdict == "OK":
            if prob_rating <= lo:
                continue
            for tag in item["problem"]["tags"]:
                good[tag] = good.get(tag, 0) + 1
                total[tag] = total.get(tag, 0) + 1
                bad.setdefault(tag, 0)
        else:
            if prob_rating >= hi:
                continue
            for tag in item["problem"]["tags"]:
                bad[tag] = bad.get(tag, 0) + 1
                total[tag] = total.get(tag, 0) + 1
                good.setdefault(tag, 0)

    return [total, good, bad]

def find_zone(total, good, bad, good_threshold=0.75, bad_threshold=0.6, prob_threshold=10):
    strong, weak, mid, nd = [], [], [], []
    for key in total:
        if good[key] / total[key] >= good_threshold and good[key] >= prob_threshold:
            strong.append(key)
        elif good[key] / total[key] <= bad_threshold and bad[key] >= prob_threshold:
            weak.append(key)
        elif good[key] >= prob_threshold:
            mid.append(key)
        else:
            nd.append(key)
    return [strong, mid, weak, nd]

def get_tag_counts(users):
    tagcount = dict()
    for user in users:
        submissions = get_submissions(user[0], 32)
        for item in submissions:
            for tag in item["problem"]["tags"]:
                tagcount[tag] = tagcount.get(tag, 0) + 1
    return dict(sorted(tagcount.items(), key=lambda item: item[1], reverse=True))

def analyze_handle(handle, progress_callback=None):
    """
    Main analysis function. Returns a dict with all results.
    progress_callback(step, message) is called to report progress.
    """
    def report(step, msg):
        if progress_callback:
            progress_callback(step, msg)

    report(0.05, "Looking up handle...")
    data = get_user(handle)
    if data["status"] != "OK":
        raise ValueError(data.get("comment", "Handle not found"))

    user_info = data["result"][0]
    rating = user_info.get("rating", 0)
    rank = user_info.get("rank", "unrated")
    max_rating = user_info.get("maxRating", 0)
    name = f"{user_info.get('firstName', '')} {user_info.get('lastName', '')}".strip() or handle

    report(0.15, f"Found {handle} (Rating: {rating}). Fetching similar users...")
    users = get_userbase(rating - 100, rating + 100, 32)

    report(0.35, "Analyzing peer submissions for tag trends...(Hold on, this might take a while)")
    tagcount = get_tag_counts(users)

    report(0.65, "Analyzing your submissions (last 800)...")
    total, good, bad = get_total_good_bad_submission(handle, 800)

    report(0.85, "Computing strong/mid/weak zones...")
    strong, mid, weak, nd = find_zone(total, good, bad)

    report(1.0, "Done!")
    return {
        "handle": handle,
        "name": name,
        "rating": rating,
        "rank": rank,
        "max_rating": max_rating,
        "tagcount": tagcount,
        "total": total,
        "good": good,
        "bad": bad,
        "strong": strong,
        "mid": mid,
        "weak": weak,
        "nd": nd,
    }


def debug():
    users = get_userbase(1500, 1600, 10)
    for user in users:
        print(user)

if __name__ == "__main__":
    debug()