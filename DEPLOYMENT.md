# Reddit Scraper Lambda - Deployment Guide

## Prerequisites

1. AWS Account
2. AWS CLI installed and configured (`aws configure`)
3. Python 3.9+

## Architecture

```
EventBridge (cron) → Lambda → DynamoDB + Telegram Bot
```

## Step 1: Create DynamoDB Table

```bash
aws dynamodb create-table \
    --table-name reddit-scraper \
    --attribute-definitions AttributeName=post_id,AttributeType=S \
    --key-schema AttributeName=post_id,KeyType=HASH \
    --billing-mode PAY_PER_REQUEST \
    --region us-east-1
```

## Step 2: Set Up Telegram Bot

1. **Create a Telegram bot:**
   - Open Telegram and search for `@BotFather`
   - Send `/newbot` and follow instructions
   - Save the **Bot Token** (looks like `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)

2. **Get your Chat ID:**
   - Start a chat with your new bot (send any message)
   - Visit: `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
   - Look for `"chat":{"id":123456789}` in the response
   - Save this **Chat ID**

3. **Store secrets in AWS Secrets Manager** (recommended):
   ```bash
   aws secretsmanager create-secret \
       --name reddit-scraper/telegram \
       --description "Telegram bot credentials" \
       --secret-string '{"bot_token":"YOUR_BOT_TOKEN","chat_id":"YOUR_CHAT_ID"}' \
       --region us-east-1
   ```

## Step 3: Package Lambda Function

```bash
# Create deployment package directory
mkdir package
cd package

# Install dependencies
pip install -r ../requirements.txt -t .

# Copy Lambda function
cp ../lambda_function.py .

# Create ZIP file
zip -r ../lambda-deployment.zip .
cd ..

# Add the lambda function to zip
zip -g lambda-deployment.zip lambda_function.py
```

## Step 4: Create IAM Role for Lambda

Create a file called `trust-policy.json`:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
```

Create the role:

```bash
aws iam create-role \
    --role-name reddit-scraper-lambda-role \
    --assume-role-policy-document file://trust-policy.json
```

Attach policies:

```bash
# Basic Lambda execution
aws iam attach-role-policy \
    --role-name reddit-scraper-lambda-role \
    --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole

# DynamoDB access
aws iam attach-role-policy \
    --role-name reddit-scraper-lambda-role \
    --policy-arn arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess

# Secrets Manager access (for Telegram credentials)
aws iam attach-role-policy \
    --role-name reddit-scraper-lambda-role \
    --policy-arn arn:aws:iam::aws:policy/SecretsManagerReadWrite
```

## Step 5: Create Lambda Function

```bash
aws lambda create-function \
    --function-name reddit-scraper \
    --runtime python3.11 \
    --role arn:aws:iam::YOUR_ACCOUNT_ID:role/reddit-scraper-lambda-role \
    --handler lambda_function.lambda_handler \
    --zip-file fileb://lambda-deployment.zip \
    --timeout 60 \
    --memory-size 256 \
    --environment Variables="{DYNAMODB_TABLE=reddit-scraper,SUBREDDIT_URL=https://www.reddit.com/r/python/,TELEGRAM_BOT_TOKEN=YOUR_BOT_TOKEN,TELEGRAM_CHAT_ID=YOUR_CHAT_ID}" \
    --region us-east-1
```

## Step 6: Create EventBridge Rule (Daily Trigger)

```bash
# Create rule that runs daily at 9 AM UTC
aws events put-rule \
    --name reddit-scraper-daily \
    --schedule-expression "cron(0 9 * * ? *)" \
    --state ENABLED \
    --region us-east-1

# Add Lambda as target
aws events put-targets \
    --rule reddit-scraper-daily \
    --targets "Id"="1","Arn"="arn:aws:lambda:us-east-1:YOUR_ACCOUNT_ID:function:reddit-scraper" \
    --region us-east-1

# Grant EventBridge permission to invoke Lambda
aws lambda add-permission \
    --function-name reddit-scraper \
    --statement-id reddit-scraper-daily-event \
    --action 'lambda:InvokeFunction' \
    --principal events.amazonaws.com \
    --source-arn arn:aws:events:us-east-1:YOUR_ACCOUNT_ID:rule/reddit-scraper-daily \
    --region us-east-1
```

## Step 7: Test the Function

```bash
# Manual test
aws lambda invoke \
    --function-name reddit-scraper \
    --region us-east-1 \
    output.json

# View output
cat output.json
```

## Customization

### Change Subreddit

Update the environment variable:

```bash
aws lambda update-function-configuration \
    --function-name reddit-scraper \
    --environment Variables="{DYNAMODB_TABLE=reddit-scraper,SUBREDDIT_URL=https://www.reddit.com/r/YOUR_SUBREDDIT/,TELEGRAM_BOT_TOKEN=YOUR_BOT_TOKEN,TELEGRAM_CHAT_ID=YOUR_CHAT_ID}"
```

### Change Schedule

Modify the cron expression:
- Daily at 9 AM UTC: `cron(0 9 * * ? *)`
- Every 6 hours: `cron(0 */6 * * ? *)`
- Every Monday at 10 AM: `cron(0 10 ? * MON *)`

## Monitoring

View logs in CloudWatch:

```bash
aws logs tail /aws/lambda/reddit-scraper --follow
```

## Cost Estimate

- DynamoDB: Free tier (25GB storage)
- Lambda: Free tier (1M requests/month)
- Telegram: Free
- Secrets Manager: $0.40/month per secret (optional - can use environment variables)
- **Total: ~$0-1/month**

## Cleanup

```bash
# Delete Lambda
aws lambda delete-function --function-name reddit-scraper

# Delete EventBridge rule
aws events remove-targets --rule reddit-scraper-daily --ids 1
aws events delete-rule --name reddit-scraper-daily

# Delete DynamoDB table
aws dynamodb delete-table --table-name reddit-scraper

# Delete Secrets Manager secret (if used)
aws secretsmanager delete-secret --secret-id reddit-scraper/telegram --force-delete-without-recovery

# Delete IAM role
aws iam detach-role-policy --role-name reddit-scraper-lambda-role --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
aws iam detach-role-policy --role-name reddit-scraper-lambda-role --policy-arn arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess
aws iam detach-role-policy --role-name reddit-scraper-lambda-role --policy-arn arn:aws:iam::aws:policy/SecretsManagerReadWrite
aws iam delete-role --role-name reddit-scraper-lambda-role
```

## Troubleshooting

**Lambda timeout**: Increase timeout in Lambda configuration
**Permission errors**: Check IAM role has correct policies
**No Telegram notifications**: Verify bot token and chat ID are correct. Test by sending a message manually to the bot.
