import json
import os
import boto3
from datetime import datetime
from decimal import Decimal
import requests
from parse_race_table import parse_race_table

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')
secrets_manager = boto3.client('secretsmanager')

# Environment variables
TABLE_NAME = "reddit-scraper"
DATA_POST_ID = "nyrr_races"
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
        current_races = scrape_race_details_from_reddit(TARGET_URL)

        # Get existing existing_data from DynamoDB
        existing_data = get_existing_data()
        # print(f"Found this record: {existing_data}")

        # Compare and find new existing_data
        differences = find_difference(current_races, existing_data)

        # Send notification
        send_notification(current_races, differences)

        # Save new existing_data to DynamoDB
        save_data(current_races)
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': f'Found differences',
                'differences_count': len(differences[0]) if differences else 0
            })
        }

    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }


def scrape_race_details_from_reddit(url):
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
        races = parse_race_table(post_data.get('selftext', ''))

        return races
    else:
        print("Error encountered while fetching Reddit data")
        return []


def get_existing_data(post_id=DATA_POST_ID):
    """
    Get existing existing_data from DynamoDB
    If post_id is provided, get that specific post
    Otherwise, get all existing_data
    """
    table = dynamodb.Table(TABLE_NAME)

    try:
        if post_id:
            # Get specific post by ID
            response = table.get_item(Key={'post_id': post_id})
            return response.get('Item', None)
        else:
            # Get all existing_data
            response = table.scan()
            return response['Items']
    except Exception as e:
        print(f"Error reading from DynamoDB: {e}")
        return None if post_id else []


def get_race_table(post_id=None):
    """
    Retrieve race table from DynamoDB
    If post_id is provided, get that specific post
    Otherwise, get the most recent one
    """
    table = dynamodb.Table(TABLE_NAME)

    try:
        if post_id:
            # Get specific post by ID (most efficient for primary key lookups)
            response = table.get_item(Key={'post_id': post_id})
            if 'Item' in response:
                return response['Item']['races']
            return None
        else:
            # Get all existing_data and return the most recent one
            response = table.scan()
            if response['Items']:
                # Sort by scraped_at timestamp (most recent first)
                sorted_items = sorted(
                    response['Items'],
                    key=lambda x: x.get('scraped_at', 0),
                    reverse=True
                )
                return sorted_items[0]['races']
            return None
    except Exception as e:
        print(f"Error retrieving race table from DynamoDB: {e}")
        return None


def get_posts_by_condition(attribute, value):
    """
    Get existing_data matching a specific condition using scan with filter
    Example: get_posts_by_condition('post_id', 'hello')

    Note: For primary key lookups, use get_item() instead (more efficient)
    """
    from boto3.dynamodb.conditions import Attr

    table = dynamodb.Table(TABLE_NAME)

    try:
        response = table.scan(
            FilterExpression=Attr(attribute).eq(value)
        )
        return response['Items']
    except Exception as e:
        print(f"Error querying DynamoDB: {e}")
        return []


def find_difference(curr_races, existing_data):
    """
    Compare current existing_data with existing ones
    Returns races that are new or modified
    """
    if not curr_races:
        return []

    if not existing_data:
        return curr_races

    try:
        existing_races = existing_data.get('races', [])

        if len(curr_races) != len(existing_races):
            print(f"Different number of races: {len(curr_races)} vs {len(existing_races)}")
            return curr_races

        differences = []

        # Compare each race in current_races with existing_races
        for i in range(len(curr_races)):
            curr_race = curr_races[i]
            existing_race = existing_races[i]

            if curr_race != existing_race:
                print(f"Difference found at index {i}")
                differences.append(curr_race)

        return differences

    except Exception as e:
        print(f"Error comparing existing_data: {e}")
        return []


def save_data(current_races, post_id=DATA_POST_ID):
    """
    Save new existing_data to DynamoDB
    """
    try:
        if not current_races:
            print("No current existing_data to save")
            return

        table = dynamodb.Table(TABLE_NAME)

        # Add timestamp for when we scraped it
        scraped_timestamp = Decimal(str(int(datetime.now().timestamp())))
        item = {
            'post_id': post_id,
            'races': current_races,
            'scraped_at': scraped_timestamp
        }
        table.put_item(Item=item)
    except Exception as e:
        print(f"Error saving to DynamoDB: {e}") 
        

def send_telegram_message(bot_token, chat_id, text):
    """Helper function to send a single Telegram message"""
    telegram_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        'chat_id': chat_id,
        'text': text,
        'parse_mode': 'HTML',
        'disable_web_page_preview': True
    }

    try:
        response = requests.post(telegram_url, json=payload)
        response.raise_for_status()
        return True
    except Exception as e:
        print(f"Error sending message: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response: {e.response.text}")
        return False


def send_notification(current_races, differences):
    """
    Send Telegram notification about new existing_data
    """
    # Get credentials
    bot_token, chat_id = get_telegram_credentials()

    if not bot_token or not chat_id:
        print("No Telegram credentials configured, skipping notification")
        return

    # Message 0: Header with timestamp
    now = datetime.now()
    date_str = now.strftime("%B %d, %Y at %I:%M %p")
    header_message = f"══════════════\n══════════════\n══════════════\n<b>📊 NYRR UPDATE</b>\n<b>{date_str}</b>\n══════════════\n══════════════\n══════════════"
    send_telegram_message(bot_token, chat_id, header_message)

    # Message 1+: All current races (batched to stay under 4096 char limit)
    header = "━━━━━━━━━━━━━━━━━━\n<b>All Current Races:</b>\n\n"
    current_batch = header
    batch_count = 0

    for race in current_races:
        race_name = race.get('race_name', 'N/A')
        date = race.get('date', 'N/A')
        release_date = race.get('release_date', 'N/A')

        race_text = f"<b>{race_name}</b>\nDate: {date}\nRelease Date: {release_date}\n\n"

        # Check if adding this race would exceed limit
        if len(current_batch) + len(race_text) > 4000:  # Leave some buffer
            send_telegram_message(bot_token, chat_id, current_batch)
            batch_count += 1
            current_batch = f"<b>All Current Races (continued {batch_count}):</b>\n\n" + race_text
        else:
            current_batch += race_text

    # Send remaining batch
    if current_batch:
        send_telegram_message(bot_token, chat_id, current_batch)

    # Last Message: Differences/Changes
    diff_lines = []
    if differences:
        diff_lines.append("🔔 NYRR Race Schedule Updated!\n")
        diff_lines.append("Changed races:")
        for diff in differences:
            race_name = diff.get('race_name', 'N/A')
            date = diff.get('date', 'N/A')
            release_date = diff.get('release_date', 'N/A')
            notes = diff.get('notes', '')

            race_text = f"<b>{race_name}</b>\n📅 <b>Date:</b> {date}\n🚨 <b><u>RELEASE DATE: {release_date}</u></b>"
            if notes:
                race_text += f"\n📝 {notes}"

            diff_lines.append(race_text)
    else:
        diff_lines.append("✅ No changes detected")

    send_telegram_message(bot_token, chat_id, '\n'.join(diff_lines))

    print("All Telegram notifications sent successfully")


lambda_handler({}, {})