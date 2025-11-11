import json
import os
from datetime import datetime
import requests
from parse_race_table import parse_race_table

# Environment variables
TARGET_URL = os.environ.get('TARGET_URL', 'https://www.reddit.com/r/RunNYC/comments/1nyv8sr/nyrr_91_in_2026_faqs_megathread/')
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID', '')
GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN', '')
GIST_ID = os.environ.get('GIST_ID', '')


def scrape_race_details_from_reddit(url):
    """
    Scrape Reddit post and extract race table
    Returns list with the post data including extracted table
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
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


def get_existing_data():
    """Get existing race data from GitHub Gist"""
    if not GITHUB_TOKEN or not GIST_ID:
        print("No Gist credentials configured")
        return None

    try:
        headers = {
            'Authorization': f'token {GITHUB_TOKEN}',
            'Accept': 'application/vnd.github.v3+json'
        }
        response = requests.get(f'https://api.github.com/gists/{GIST_ID}', headers=headers)
        response.raise_for_status()

        gist_data = response.json()
        # Get the first file in the gist
        filename = list(gist_data['files'].keys())[0]
        content = gist_data['files'][filename]['content']

        return json.loads(content)
    except Exception as e:
        print(f"Error fetching from Gist: {e}")
        return None


def save_data(current_races):
    """Save race data to GitHub Gist"""
    if not GITHUB_TOKEN or not GIST_ID:
        print("No Gist credentials configured, skipping save")
        return

    data = {
        'races': current_races,
        'scraped_at': datetime.now().isoformat()
    }

    try:
        headers = {
            'Authorization': f'token {GITHUB_TOKEN}',
            'Accept': 'application/vnd.github.v3+json'
        }

        payload = {
            'files': {
                'nyrr_races.json': {
                    'content': json.dumps(data, indent=2)
                }
            }
        }

        response = requests.patch(f'https://api.github.com/gists/{GIST_ID}',
                                 headers=headers,
                                 json=payload)
        response.raise_for_status()
        print(f"Saved {len(current_races)} races to Gist")
    except Exception as e:
        print(f"Error saving to Gist: {e}")
        raise


def find_difference(curr_races, existing_data):
    """
    Compare current races with existing ones
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
        print(f"Error comparing data: {e}")
        return []


def send_telegram_message(text):
    """Helper function to send a single Telegram message"""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("No Telegram credentials configured, skipping notification")
        return False

    telegram_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        'chat_id': TELEGRAM_CHAT_ID,
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
    """Send Telegram notification about race data"""
    # Message 0: Header with timestamp
    now = datetime.now()
    date_str = now.strftime("%B %d, %Y at %I:%M %p")
    header_message = f"══════════════\n══════════════\n══════════════\n<b>📊 NYRR UPDATE</b>\n<b>{date_str}</b>\n══════════════\n══════════════\n══════════════"
    send_telegram_message(header_message)

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
            send_telegram_message(current_batch)
            batch_count += 1
            current_batch = f"<b>All Current Races (continued {batch_count}):</b>\n\n" + race_text
        else:
            current_batch += race_text

    # Send remaining batch
    if current_batch:
        send_telegram_message(current_batch)

    # Last Message: Differences/Changes (batched if needed)
    if differences:
        diff_header = "🚨🚨🚨🚨🚨🚨🚨🚨🚨\n<b>🔔 NYRR RACE SCHEDULE UPDATED! 🔔</b>\n🚨🚨🚨🚨🚨🚨🚨🚨🚨\n\n<b>CHANGED RACES:</b>\n\n"
        diff_batch = diff_header
        diff_batch_count = 0

        for diff in differences:
            race_name = diff.get('race_name', 'N/A')
            date = diff.get('date', 'N/A')
            release_date = diff.get('release_date', 'N/A')
            notes = diff.get('notes', '')

            race_text = f"<b>{race_name}</b>\n📅 <b>Date:</b> {date}\n🚨 <b><u>RELEASE DATE: {release_date}</u></b>"
            if notes:
                race_text += f"\n📝 {notes}"
            race_text += "\n\n"

            # Check if adding this race would exceed limit
            if len(diff_batch) + len(race_text) > 4000:
                send_telegram_message(diff_batch)
                diff_batch_count += 1
                diff_batch = f"🔔 <b>Changed races (continued {diff_batch_count}):</b>\n\n" + race_text
            else:
                diff_batch += race_text

        # Send remaining batch
        if diff_batch:
            send_telegram_message(diff_batch)
    else:
        send_telegram_message("✅ No changes detected")

    print("All Telegram notifications sent successfully")


def main():
    """Main function"""
    print(f"Starting Reddit scraper for: {TARGET_URL}")

    try:
        # Fetch current Reddit data
        current_races = scrape_race_details_from_reddit(TARGET_URL)
        print(f"Fetched {len(current_races)} races from Reddit")

        # Get existing data
        existing_data = get_existing_data()

        # Compare and find differences
        differences = find_difference(current_races, existing_data)
        print(f"Found {len(differences)} differences")

        # Send notification
        send_notification(current_races, differences)

        # Save new data
        save_data(current_races)

        print("✅ Scraper completed successfully")

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        raise


if __name__ == "__main__":
    main()
