# Local Cron Setup Guide

Run the NYRR scraper locally on your Mac using cron. No cloud services needed!

## Benefits
- ✅ No Reddit IP blocking
- ✅ 100% free
- ✅ Runs on your computer automatically
- ✅ Simple setup

## Prerequisites

1. Python 3.9+ installed
2. Your computer needs to be on when cron runs
3. Telegram bot token and chat ID

## Setup Instructions

### 1. Install Dependencies

```bash
cd /Users/bsp/Dev/runner_high
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Create .env File

Create a file called `.env` in the project directory:

```bash
cp .env.example .env
```

Edit `.env` and add your credentials:

```
TELEGRAM_BOT_TOKEN=8433824682:AAETjIcPbuTMkvSlIWhTAo_XVHVIwSd7Lao
TELEGRAM_CHAT_ID=your_chat_id_here
TARGET_URL=https://www.reddit.com/r/RunNYC/comments/1nyv8sr/nyrr_91_in_2026_faqs_megathread/
```

**Note:** Data is stored locally in `race_data.json` - no need for GitHub Gist or tokens!

### 3. Test the Script

Run manually to make sure it works:

```bash
./run_scraper.sh
```

You should see:
- Fetched races from Reddit
- Saved to Gist
- Telegram messages sent

### 4. Set Up Cron Job

Open cron editor:

```bash
crontab -e
```

Add this line to run every 6 hours:

```bash
0 */6 * * * /Users/bsp/Dev/runner_high/run_scraper.sh >> /Users/bsp/Dev/runner_high/scraper.log 2>&1
```

**Cron schedule examples:**
```bash
0 */6 * * *    # Every 6 hours
0 9 * * *      # Daily at 9 AM
0 9,21 * * *   # Twice daily (9 AM and 9 PM)
0 */12 * * *   # Every 12 hours
```

Save and exit (in vim: press `Esc`, type `:wq`, press Enter)

### 5. Verify Cron Job

Check if cron job was added:

```bash
crontab -l
```

You should see your cron job listed.

### 6. Monitor Logs

View the log file to see execution history:

```bash
# View entire log
cat scraper.log

# View last 20 lines
tail -20 scraper.log

# Watch live (follow mode)
tail -f scraper.log
```

## Troubleshooting

**Cron job not running:**
- Make sure your computer is on at scheduled time
- Check system logs: `grep CRON /var/log/system.log`
- Verify cron has correct permissions

**Script fails:**
- Check `scraper.log` for errors
- Run `./run_scraper.sh` manually to see errors
- Verify .env file has correct values

**No Telegram messages:**
- Verify bot token and chat ID in .env
- Check scraper.log for errors

**Reddit blocking:**
- Shouldn't happen locally, but if it does:
  - Add delays between runs (change cron schedule)
  - Try old.reddit.com in TARGET_URL

## Disabling Cron Job

To stop automatic runs:

```bash
crontab -e
```

Add `#` at the beginning of the line to comment it out:

```bash
# 0 */6 * * * /Users/bsp/Dev/runner_high/run_scraper.sh >> /Users/bsp/Dev/runner_high/scraper.log 2>&1
```

Or remove the line completely.

## Files

- `run_scraper.sh` - Main runner script
- `.env` - Your credentials (git ignored)
- `.env.example` - Template for .env
- `scraper.log` - Execution log (auto-created)
- `main.py` - Scraper code

## Keeping Computer Awake

If your Mac sleeps, cron won't run. Options:

1. **Use caffeinate** (keeps Mac awake):
   ```bash
   caffeinate -s &
   ```

2. **System Preferences**:
   - System Settings → Energy Saver
   - Prevent automatic sleeping when display is off

3. **Use a different schedule**:
   - Schedule cron for times when you're using the computer

## Alternative: launchd (More reliable on Mac)

macOS prefers launchd over cron. If cron gives issues, I can help set up a launchd plist file instead.

---

# Raspberry Pi Setup Guide

Run the scraper 24/7 on a Raspberry Pi - perfect for always-on operation!

## What You Need

### Hardware (you have the Pi 5!)
- ✅ Raspberry Pi 5 (what you bought)
- 🔌 USB-C power supply (27W official recommended)
- 💾 MicroSD card (32GB or larger, Class 10 or better)
- 🖥️ For initial setup only:
  - Monitor + micro HDMI cable (or use headless setup)
  - USB keyboard
  - OR just do headless setup (no monitor needed)

### Software
- Raspberry Pi Imager (free download)

## Step-by-Step Setup

### 1. Install Raspberry Pi OS

**On your Mac:**

1. **Download Raspberry Pi Imager:**
   - Go to https://www.raspberrypi.com/software/
   - Download and install for macOS

2. **Flash the OS:**
   - Insert SD card into your Mac (use adapter if needed)
   - Open Raspberry Pi Imager
   - Choose Device: **Raspberry Pi 5**
   - Choose OS: **Raspberry Pi OS Lite (64-bit)** (no desktop needed)
   - Choose Storage: Your SD card
   - Click **Next**

3. **Configure settings (IMPORTANT!):**
   - Click "Edit Settings" when prompted
   - **General tab:**
     - Set hostname: `raspberrypi` (or whatever you want)
     - Set username: `pi`
     - Set password: (choose a password)
     - Configure WiFi:
       - SSID: Your WiFi network name
       - Password: Your WiFi password
       - Country: US
     - Set locale: America/New_York (or your timezone)
   - **Services tab:**
     - ✅ Enable SSH (USE PASSWORD AUTHENTICATION)
   - Click "Save"
   - Click "Yes" to apply settings
   - Click "Yes" to erase SD card

4. **Wait for it to finish** (takes 5-10 minutes)

5. **Eject SD card and insert into Raspberry Pi**

6. **Power on the Pi** (plug in power)
   - Wait 2-3 minutes for first boot
   - It will automatically connect to WiFi

### 2. Connect to Your Pi

**Find the Pi's IP address:**

Option A - If you have a monitor connected:
```bash
# On the Pi, log in and type:
hostname -I
```

Option B - From your Mac:
```bash
# Try connecting by hostname:
ssh pi@raspberrypi.local

# If that doesn't work, find IP on your network:
ping raspberrypi.local
# Or check your router's device list
```

**Connect via SSH from your Mac:**
```bash
ssh pi@raspberrypi.local
# Or: ssh pi@192.168.1.XXX (use the IP you found)
```

Enter the password you set during imaging.

### 3. Set Up the Pi

**Update the system:**
```bash
sudo apt update
sudo apt upgrade -y
```

**Install Python and dependencies:**
```bash
sudo apt install -y python3-pip python3-venv git
```

### 4. Transfer Your Project

**Option A - Using SCP from your Mac:**
```bash
# On your Mac (in a new terminal):
cd /Users/bsp/Dev
scp -r runner_high pi@raspberrypi.local:/home/pi/
```

**Option B - Clone from Git (if you pushed to GitHub):**
```bash
# On the Pi:
cd /home/pi
git clone https://github.com/YOUR_USERNAME/runner_high.git
```

### 5. Set Up the Project on Pi

**SSH into your Pi and set up:**
```bash
ssh pi@raspberrypi.local

cd /home/pi/runner_high

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 6. Create .env File on Pi

**Create the .env file:**
```bash
nano .env
```

**Add your credentials:**
```
TARGET_URL=https://www.reddit.com/r/RunNYC/comments/1nyv8sr/nyrr_91_in_2026_faqs_megathread/
```

Save and exit: `Ctrl+X`, then `Y`, then `Enter`

### 7. Test the Script

```bash
./run_scraper.sh
```

You should see it fetch races and send Telegram messages!

### 8. Set Up Cron on Pi

**Edit crontab:**
```bash
crontab -e
```

If asked to choose an editor, select `nano` (usually option 1).

**Add this line:**
```bash
0 */6 * * * /home/pi/runner_high/run_scraper.sh >> /home/pi/runner_high/scraper.log 2>&1
```

Save and exit: `Ctrl+X`, then `Y`, then `Enter`

**Verify it was added:**
```bash
crontab -l
```

### 9. Done! 🎉

Your Pi is now running 24/7! You can:

- **Unplug monitor/keyboard** - it runs headless now
- **Close SSH** - it will keep running
- **Just leave it plugged in** - uses only ~5W of power

## Managing Your Pi

### Access logs remotely:
```bash
ssh pi@raspberrypi.local
tail -20 /home/pi/runner_high/scraper.log
```

### Stop the Pi safely:
```bash
ssh pi@raspberrypi.local
sudo shutdown now
```

### Restart the Pi:
```bash
ssh pi@raspberrypi.local
sudo reboot
```

### Update the code:
```bash
ssh pi@raspberrypi.local
cd /home/pi/runner_high
git pull  # If using Git
# Or copy new files with SCP from your Mac
```

## Raspberry Pi Troubleshooting

**Can't SSH to Pi:**
- Make sure Pi is powered on (green LED should be blinking)
- Check your router to see if Pi is connected
- Try IP address instead of hostname: `ssh pi@192.168.1.XXX`
- Wait 2-3 minutes after boot before trying SSH

**Script not running:**
- Check logs: `cat /home/pi/runner_high/scraper.log`
- Make sure script is executable: `chmod +x /home/pi/runner_high/run_scraper.sh`
- Verify cron job: `crontab -l`

**WiFi issues:**
- Reconnect to WiFi: `sudo raspi-config` → System Options → Wireless LAN
- Check connection: `ping google.com`

**Want to access Pi from anywhere:**
- Set up port forwarding on your router
- Or use Tailscale (free VPN for personal use)

## Power Usage

- Raspberry Pi 5 uses ~3-5W when idle
- ~8-10W under load
- Costs approximately **$5-8 per year** to run 24/7

## Next Steps

Once it's running for a few days and you see it working:
- You can put the Pi anywhere with power + WiFi
- No monitor/keyboard needed
- Just leave it running!

**Optional improvements:**
- Get a case for the Pi
- Add a heatsink/fan if it gets hot
- Set up automatic updates
- Monitor Pi health with scripts
