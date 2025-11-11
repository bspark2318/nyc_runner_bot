# GitHub Actions Setup Guide

## Overview

This setup runs the NYRR race scraper automatically using GitHub Actions instead of AWS Lambda. Benefits:
- ✅ Free (2000 minutes/month on free tier)
- ✅ No Reddit IP blocking issues
- ✅ Simple JSON file storage (no DynamoDB needed)
- ✅ Easy to monitor and debug

## Setup Instructions

### 1. Push Code to GitHub

```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/runner_high.git
git push -u origin main
```

### 2. Create a GitHub Gist for Data Storage

1. Go to https://gist.github.com/
2. Click "Create secret gist" (important: must be secret!)
3. Set filename: `nyrr_races.json`
4. Set content:
   ```json
   {
     "races": [],
     "scraped_at": ""
   }
   ```
5. Click "Create secret gist"
6. Copy the Gist ID from the URL (e.g., if URL is `https://gist.github.com/username/abc123def456`, the ID is `abc123def456`)

### 3. Add GitHub Secrets

Go to your repository on GitHub: `Settings` → `Secrets and variables` → `Actions` → `New repository secret`

Add these secrets:

1. **TELEGRAM_BOT_TOKEN**
   - Value: Your bot token from @BotFather (e.g., `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)

2. **TELEGRAM_CHAT_ID**
   - Value: Your chat ID (e.g., `123456789`)

3. **GIST_ID**
   - Value: The Gist ID you copied in step 2 (e.g., `abc123def456`)

**Note:** `GITHUB_TOKEN` is automatically provided by GitHub Actions, no need to add it!

### 4. Enable GitHub Actions

1. Go to the `Actions` tab in your repository
2. Click "I understand my workflows, go ahead and enable them"

### 5. Test the Workflow

**Manual trigger:**
1. Go to `Actions` tab
2. Click on "NYRR Race Scraper" workflow
3. Click "Run workflow" → "Run workflow"
4. Check the logs to see if it worked

### 6. Verify Data Storage

After the first run:
- Go to your secret Gist (https://gist.github.com/YOUR_USERNAME/YOUR_GIST_ID)
- The `nyrr_races.json` file should be updated with race data
- Check the revision history to see updates over time

## Schedule

The workflow runs automatically:
- **Every 6 hours** (at 00:00, 06:00, 12:00, 18:00 UTC)

To change the schedule, edit `.github/workflows/scraper.yml`:

```yaml
schedule:
  # Examples:
  - cron: '0 */6 * * *'   # Every 6 hours
  - cron: '0 9 * * *'     # Daily at 9 AM UTC
  - cron: '0 */12 * * *'  # Every 12 hours
```

## How It Works

1. **GitHub Actions triggers** on schedule or manual run
2. **Scrapes Reddit** for race data using `main.py`
3. **Fetches previous data** from your secret GitHub Gist
4. **Compares** current vs previous race data
5. **Sends Telegram notification** if changes detected
6. **Updates the Gist** with new race data

## Monitoring

### View Logs

1. Go to `Actions` tab
2. Click on a workflow run
3. Click on the "scrape" job to see detailed logs

### Common Issues

**No Telegram messages:**
- Verify secrets are set correctly
- Check workflow logs for errors

**Workflow not running:**
- Ensure GitHub Actions is enabled
- Check if repository is public (private repos have limited free minutes)

**Reddit blocking:**
- GitHub Actions IPs are usually not blocked by Reddit
- If blocked, the workflow will show an error in logs

## Files

- `.github/workflows/scraper.yml` - Workflow definition
- `main.py` - Main scraper script (uses GitHub Gist for storage)
- `parse_race_table.py` - Reddit table parser
- `requirements.txt` - Python dependencies

**Data Storage:** Stored in a secret GitHub Gist (not in the repository)

## Cost

**FREE** on GitHub's free tier:
- Public repos: Unlimited minutes
- Private repos: 2000 minutes/month (each run takes ~1 minute)

## Advantages over AWS Lambda

1. ✅ No Reddit IP blocking
2. ✅ Completely free for public repos
3. ✅ Simpler setup (no DynamoDB, IAM, etc.)
4. ✅ Easy to debug with workflow logs
5. ✅ Data stored in Gist (clean, version-controlled)
6. ✅ Can run manual tests anytime
7. ✅ No complex cloud infrastructure needed
