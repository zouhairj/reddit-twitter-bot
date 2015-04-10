# -*- coding: utf-8 -*-

"""
Copyright 2015 Randal S. Olson

This file is part of the reddit Twitter Bot library.

The reddit Twitter Bot library is free software: you can redistribute it and/or
modify it under the terms of the GNU General Public License as published by the
Free Software Foundation, either version 3 of the License, or (at your option) any
later version.

The reddit Twitter Bot library is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
You should have received a copy of the GNU General Public License along with the reddit
Twitter Bot library. If not, see http://www.gnu.org/licenses/.
"""

import praw
import json
import requests
import tweepy
import time
import os.path

# Place your Twitter API keys here
access_token = ""
access_token_secret = ""
consumer_key = ""
consumer_secret = ""

# Place your Google API key here
google_api_key = ""

# Place the subreddit you want to look up posts from here
subreddit_to_monitor = "dataisbeautiful"

def setup_connection_reddit(subreddit):
    """ Creates a connection to the reddit API. """
    print("[bot] Setting up connection with reddit")
    r = praw.Reddit("reddit Twitter bot monitoring %s" % (subreddit)) 
    subreddit = r.get_subreddit(subreddit)
    return subreddit
    
def tweet_creator(subreddit_info):
    """ Looks up posts from reddit and shortens the URLs to them. """
    post_dict = {}
    post_ids = []
    print("[bot] Getting posts from reddit")
    
    # You can use the following "get" functions to get posts from reddit:
    #   - get_top(): gets the most-upvoted posts (ignoring the age of the post)
    #   - get_hot(): gets the most-upvoted posts (taking the age of the post into account)
    #   - get_new(): gets the newest posts
    #
    # The "limit" parameter tells the API the maximum number of posts to look up
    
    for submission in subreddit_info.get_hot(limit=5):
        if already_tweeted(submission.id):
            # This stores a link to the reddit post itself
            # If you want to link to what the post is linking to instead, use
            # "submission.url" instead of "submission.permanlink"
            post_dict[strip_title(submission.title)] = submission.permalink
            post_ids.append(submission.id)
        else:
            print("[bot] Already posted: " + str(submission))
            
    shortened_post_dict = {}

    if len(post_dict.keys()) > 0:
        print("[bot] Generating short link using goo.gl")

        for post in post_dict:
            post_title = post
            post_link = post_dict[post]
            short_link = shorten(post_link)
            shortened_post_dict[post_title] = short_link

    return shortened_post_dict, post_ids
    
def already_tweeted(id):
    """ Checks if the reddit Twitter bot has already tweeted a post. """
    found = False
    with open("posted_posts.txt", "r") as file:
        for line in file:
            if id in line:
                found = True
                break
    return found

def strip_title(title):
    """ Shortens the title of the post so it fits within the 140 character limit. """
    
    # How much you strip from the title depends on how much extra text
    # (URLs, hashtags, etc.) that you add to the tweet
    if len(title) < 106:
        return title
    else:
        return title[:105] + "..."

def shorten(url):
    """ Shortens the given URL using the Google URL shortening API. """
    headers = {"content-type": "application/json"}
    payload = {"longUrl": url}
    url = "https://www.googleapis.com/urlshortener/v1/url?key=%s" % (google_api_key)
    r = requests.post(url, data=json.dumps(payload), headers=headers)
    link = json.loads(r.text)["id"]
    return link

def tweeter(post_dict, post_ids):
    """ Tweets all of the selected reddit posts. """
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)
    api = tweepy.API(auth)
    for post, post_id in zip(post_dict, post_ids):
        post_text = post + " " + post_dict[post] + " #dataviz"
        print("[bot] Posting this link on Twitter")
        print(post_text)
        api.update_status(post_text)
        log_tweet(post_id)
        time.sleep(30)

def log_tweet(id):
    """ Takes note of when the reddit Twitter bot tweeted a post. """
    with open("posted_posts.txt", "a") as out_file:
        out_file.write(str(id) + "\n")

def main():
    # If the tweet tracking file does not already exist, create it
    if not os.path.exists("posted_posts.txt"):
        with open("posted_posts.txt", "w"):
            pass

    subreddit = setup_connection_reddit(subreddit_to_monitor)
    post_dict, post_ids = tweet_creator(subreddit)
    tweeter(post_dict, post_ids)
        
if __name__ == "__main__":
    main()
