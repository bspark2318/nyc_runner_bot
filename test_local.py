"""
Local testing script for Reddit scraper
Run this to test the scraping logic without deploying to AWS
"""
import requests
import json

SUBREDDIT_URL = 'https://www.reddit.com/r/python/'

def scrape_reddit(url):
    """Test the Reddit scraping function"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (compatible; RedditScraper/1.0)'
    }

    json_url = url.rstrip('/') + '.json'
    print(f"Fetching: {json_url}")

    response = requests.get(json_url, headers=headers)
    response.raise_for_status()

    data = response.json()
    posts = []

    for child in data['data']['children']:
        post_data = child['data']
        posts.append({
            'post_id': post_data['id'],
            'title': post_data['title'],
            'author': post_data['author'],
            'url': post_data['url'],
            'permalink': f"https://reddit.com{post_data['permalink']}",
            'score': post_data['score'],
            'created_utc': int(post_data['created_utc'])
        })

    return posts

if __name__ == '__main__':
    print("Testing Reddit scraper locally...\n")

    try:
        posts = scrape_reddit(SUBREDDIT_URL)
        print(f"✓ Successfully scraped {len(posts)} posts\n")

        print("Sample posts:")
        for i, post in enumerate(posts[:3], 1):
            print(f"\n{i}. {post['title']}")
            print(f"   Author: {post['author']}")
            print(f"   Score: {post['score']}")
            print(f"   URL: {post['permalink']}")

        print(f"\n✓ Test passed! Ready to deploy to Lambda.")

    except Exception as e:
        print(f"✗ Error: {e}")
