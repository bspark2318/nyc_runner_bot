import json
import os
import boto3
from datetime import datetime
from decimal import Decimal
import requests
from bs4 import BeautifulSoup
from parse_race_table import parse_race_table

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')
secrets_manager = boto3.client('secretsmanager')

# Environment variables
TABLE_NAME = "reddit-scraper"
TARGET_URL = os.environ.get('TARGET_URL', 'https://www.reddit.com/r/RunNYC/comments/1nyv8sr/nyrr_91_in_2026_faqs_megathread/')
SECRET_NAME = os.environ.get('SECRET_NAME', 'reddit-scraper/telegram')

def get_telegram_credentials():
    """
    Get Telegram credentials from Secrets Manager or fall back to environment variables
    """
    # Try Secrets Manager first
    try:
        response = secrets_manager.get_secret_value(SecretId=SECRET_NAME)
        secret = json.loads(response['SecretString'])
        bot_token = secret.get('bot_token', '')
        chat_id = secret.get('chat_id', '')
        print("Retrieved Telegram credentials from Secrets Manager")
        return bot_token, chat_id
    except Exception as e:
        print(f"Could not retrieve from Secrets Manager: {e}")
        raise ValueError("Telegram credentials not found in Secrets Manager")

def lambda_handler(event, context):
    """
    Main Lambda handler - runs on schedule to check Reddit for new comments
    """
    print(f"Starting Reddit scraper for: {TARGET_URL}")

    try:
        # Fetch current Reddit comments
        current_posts = scrape_reddit(TARGET_URL)
        print(current_posts)
        print(f"Found {len(current_posts)} comments")

        # Get existing posts from DynamoDB
        existing_posts = get_existing_posts()
        print(f"Found {len(existing_posts)} existing posts in DB")

        # Compare and find new posts
        new_posts = find_new_posts(current_posts, existing_posts)

        if new_posts:

            # Save new posts to DynamoDB
            save_posts(new_posts)

            # Send notification
            send_notification(new_posts)

            return {
                'statusCode': 200,
                'body': json.dumps({
                    'message': f'Found {len(new_posts)} new posts',
                    'new_posts': len(new_posts)
                })
            }
        else:
            print("No new posts found")
            return {
                'statusCode': 200,
                'body': json.dumps({'message': 'No new posts found'})
            }

    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }


def extract_race_table(selftext):
    """
    Extract the race schedule table from Reddit post selftext
    Returns the markdown table as a string
    """
    import re

    # Find the table that starts with |Race|Date|Release Date|Notes|
    table_pattern = r'\|Race\|Date\|Release Date\|Notes\|.*?(?=\n\n|\Z)'
    match = re.search(table_pattern, selftext, re.DOTALL)

    if match:
        return match.group(0).strip()
    return None


def scrape_reddit(url):
    """
    Scrape Reddit post and extract race table
    Returns list with the post data including extracted table
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    # Add .json to get Reddit's JSON API
    json_url = url.rstrip('/') + '.json'

    response = requests.get(json_url, headers=headers)
    response.raise_for_status()

    data = response.json()

    # For a post URL, Reddit returns [post_data, comments_data]
    if isinstance(data, list) and len(data) >= 2:
        post_data = data[0]['data']['children'][0]['data']

        # Extract the race table from the post selftext
        race_table = extract_race_table(post_data.get('selftext', ''))
        formatted_table = parse_race_table(race_table)
        print(formatted_table)

        return [{
            'post_id': post_data['id'],
            'race_table': race_table
        }]
    else:
        # Fallback for subreddit listing
        posts = []
        for child in data['data']['children']:
            post_data = child['data']
            race_table = extract_race_table(post_data.get('selftext', ''))
            
            posts.append({
                'post_id': post_data['id'],
                'race_table': race_table
            })
        return posts


def get_existing_posts():
    """
    Get all existing post/comment IDs from DynamoDB
    """
    table = dynamodb.Table(TABLE_NAME)

    try:
        response = table.scan(
            ProjectionExpression='post_id'
        )
        return set(item['post_id'] for item in response['Items'])
    except Exception as e:
        print(f"Error reading from DynamoDB: {e}")
        # If table doesn't exist yet, return empty set
        return set()


def find_new_posts(current_posts, existing_post_ids):
    """
    Compare current posts with existing ones
    """
    return [post for post in current_posts if post['post_id'] not in existing_post_ids]


def save_posts(posts):
    """
    Save new posts to DynamoDB
    """
    table = dynamodb.Table(TABLE_NAME)

    for post in posts:
        # Add timestamp for when we scraped it
        post['scraped_at'] = int(datetime.now().timestamp())

        # DynamoDB doesn't support float, convert to Decimal
        post['score'] = Decimal(str(post['score']))
        post['created_utc'] = Decimal(str(post['created_utc']))
        post['scraped_at'] = Decimal(str(post['scraped_at']))

        table.put_item(Item=post)
        print(f"Saved post: {post['post_id']} - {post['title']}")


def send_notification(new_posts):
    """
    Send Telegram notification about new posts
    """
    # Get credentials
    bot_token, chat_id = get_telegram_credentials()

    if not bot_token or not chat_id:
        print("No Telegram credentials configured, skipping notification")
        return

    # Format message
    message_lines = [f"🔔 Found {len(new_posts)} new Reddit comments!\n"]

    for post in new_posts[:5]:  # Limit to first 5 comments
        message_lines.append(f"• {post['author']}: {post['title']}")
        message_lines.append(f"  {post['permalink']}\n")

    if len(new_posts) > 5:
        message_lines.append(f"... and {len(new_posts) - 5} more comments")

    message = '\n'.join(message_lines)

    # Send via Telegram Bot API
    telegram_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

    payload = {
        'chat_id': chat_id,
        'text': message,
        'parse_mode': 'HTML',
        'disable_web_page_preview': True
    }

    try:
        response = requests.post(telegram_url, json=payload)
        response.raise_for_status()
        print("Telegram notification sent successfully")
    except Exception as e:
        print(f"Error sending Telegram notification: {e}")




scrape_reddit(TARGET_URL)