# Binance New Listings Monitor

A Google Cloud Function that monitors Binance's cryptocurrency listing announcements and sends notifications to Slack. Get instant alerts when new cryptocurrencies are listed on Binance.

## Features

- 🔍 Monitors Binance's new cryptocurrency listings page
- 📱 Sends notifications to Slack with mobile alerts
- 🔄 Runs every 30 minutes via Cloud Scheduler
- 💾 Prevents duplicate notifications using Google Cloud Storage
- 🚀 Easy deployment to Google Cloud Functions

## Prerequisites

- Google Cloud Platform account
- Slack workspace with permissions to create webhooks
- Python 3.9 or newer

## Setup

### 1. Create a Slack Webhook

1. Go to your Slack workspace settings
2. Navigate to Custom Integrations > Incoming Webhooks
3. Create a new webhook for your desired channel
4. Copy the webhook URL for later use

### 2. Google Cloud Setup

1. Create a new Google Cloud project (or use an existing one)
2. Enable the following APIs:
   - Cloud Functions API
   - Cloud Scheduler API
   - Cloud Storage API
3. Create a Google Cloud Storage bucket:
   ```bash
   gsutil mb gs://your-bucket-name
   ```

### 3. Deployment

1. Clone this repository:
   ```bash
   git clone https://github.com/yourusername/binance-listings-monitor.git
   cd binance-listings-monitor
   ```

2. Deploy the Cloud Function:
   ```bash
   gcloud functions deploy binance-monitor \
     --runtime python39 \
     --trigger-http \
     --entry-point check_new_listings \
     --set-env-vars "SLACK_WEBHOOK_URL=your_webhook_url,GCS_BUCKET_NAME=your_bucket_name"
   ```

3. Create a Cloud Scheduler job:
   ```bash
   gcloud scheduler jobs create http binance-monitor-job \
     --schedule="*/30 * * * *" \
     --uri="YOUR_CLOUD_FUNCTION_URL" \
     --http-method="POST"
   ```

## Environment Variables

- `SLACK_WEBHOOK_URL`: Your Slack webhook URL
- `GCS_BUCKET_NAME`: Name of your Google Cloud Storage bucket (without gs:// prefix)

## Local Development

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Set environment variables:
   ```bash
   export SLACK_WEBHOOK_URL="your_webhook_url"
   export GCS_BUCKET_NAME="your_bucket_name"
   ```

3. Run the script:
   ```bash
   python binance-latest-crypto.py
   ```

## File Structure

```
├── binance-latest-crypto.py # Main Cloud Function code
├── requirements.txt     # Python dependencies
└── README.md           # This file
```

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

## License

[MIT](https://choosealicense.com/licenses/mit/)

## Acknowledgments

- Built using Google Cloud Platform
- Uses Binance's public announcements page
- Slack for notifications