import requests
from datetime import datetime
import json
import re
import os
from google.cloud import storage

def get_latest_sent_id(bucket_name, filename="latest_article_id.txt"):
    """
    Retrieve the ID of the last article sent to Slack from Google Cloud Storage.
    This helps prevent duplicate notifications.
    
    Args:
        bucket_name (str): Name of the GCS bucket
        filename (str): Name of the file storing the latest article ID
        
    Returns:
        str or None: The last sent article ID if found, None if file doesn't exist
    """
    try:
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(filename)
        
        if not blob.exists():
            print("No previous article ID found in storage")
            return None
            
        return blob.download_as_text().strip()
    except Exception as e:
        print(f"Error reading from Cloud Storage: {e}")
        return None

def save_latest_sent_id(bucket_name, article_id, filename="latest_article_id.txt"):
    """
    Save the latest sent article ID to Google Cloud Storage.
    This records what we've already notified about.
    
    Args:
        bucket_name (str): Name of the GCS bucket
        article_id (str): ID of the article to save
        filename (str): Name of the file to store the ID
        
    Returns:
        bool: True if save was successful, False otherwise
    """
    try:
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(filename)
        blob.upload_from_string(str(article_id))
        print(f"Saved article ID {article_id} to Cloud Storage")
        return True
    except Exception as e:
        print(f"Error saving to Cloud Storage: {e}")
        return False

def send_to_slack(webhook_url, article):
    """
    Send formatted article information to Slack using their Block Kit format.
    Uses @here mention to ensure mobile notifications are triggered.
    
    Args:
        webhook_url (str): Slack webhook URL
        article (dict): Article information containing title, url, timestamp, and id
        
    Returns:
        bool: True if message was sent successfully, False otherwise
    """
    slack_message = {
        "text": "<!here> New Binance Listing Alert! 🚨",  # Fallback and notification text
        "blocks": [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "🚨 New Binance Listing Alert! 🚨",
                    "emoji": True
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*{article['title']}*"
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Time:*\n{article['timestamp'].strftime('%Y-%m-%d %H:%M:%S UTC')}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*ID:*\n{article['id']}"
                    }
                ]
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"<{article['url']}|Click here to view the announcement> 🔗"
                }
            }
        ]
    }

    try:
        response = requests.post(
            webhook_url,
            json=slack_message,
            headers={'Content-Type': 'application/json'}
        )
        response.raise_for_status()
        print("Successfully sent to Slack")
        return True
    except Exception as e:
        print(f"Failed to send to Slack: {e}")
        return False

def fetch_new_listings():
    """
    Scrape the latest cryptocurrency listing announcement from Binance's website.
    Uses their embedded JavaScript data structure to get the information.
    
    Returns:
        dict or None: Article information if found, None if error occurs
            Contains keys: id, title, url, timestamp
    """
    try:
        webpage_url = 'https://www.binance.com/en/support/announcement/new-cryptocurrency-listing?c=48'
        webpage_response = requests.get(webpage_url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'
        })
        webpage_response.raise_for_status()
        
        # Extract the embedded JSON data from the page's script tag
        data_pattern = re.compile(r'<script id="__APP_DATA"[^>]*>(.*?)</script>', re.DOTALL)
        match = data_pattern.search(webpage_response.text)
        if not match:
            return None
            
        try:
            # Navigate through Binance's data structure to find the articles
            page_data = json.loads(match.group(1))
            route_data = page_data.get('appState', {}).get('loader', {}).get('dataByRouteId', {})
            
            # Find the route containing the cryptocurrency listings
            for route_id, data in route_data.items():
                if 'catalogDetail' in data:
                    articles = data['catalogDetail'].get('articles', [])
                    if articles:
                        latest = articles[0]
                        return {
                            'id': str(latest['id']),
                            'title': latest['title'],
                            'url': f"https://www.binance.com/en/support/announcement/{latest['code']}",
                            'timestamp': datetime.fromtimestamp(latest['releaseDate']/1000)
                        }
                
        except Exception as e:
            print(f"Error processing data: {e}")
                
    except Exception as e:
        print(f"Error fetching webpage: {e}")
    
    return None

def check_new_listings(event, context):
    """
    Cloud Function entry point. Checks for new Binance listings and sends notifications.
    
    Required environment variables:
        SLACK_WEBHOOK_URL: Webhook URL for Slack notifications
        GCS_BUCKET_NAME: Name of the Google Cloud Storage bucket (without gs:// prefix)
    
    Args:
        event: Cloud Function event data
        context: Cloud Function context
        
    Returns:
        bool: True if execution was successful, False if any error occurred
    """
    # Get configuration from environment variables
    slack_webhook_url = os.environ.get('SLACK_WEBHOOK_URL')
    bucket_name = os.environ.get('GCS_BUCKET_NAME')
    
    if not slack_webhook_url or not bucket_name:
        print("Error: Required environment variables not set")
        return False

    # Fetch the latest listing from Binance
    latest_article = fetch_new_listings()
    if not latest_article:
        print("Failed to fetch latest listing")
        return False
        
    print("\nLatest cryptocurrency listing found:")
    print(f"Title: {latest_article['title']}")
    print(f"URL: {latest_article['url']}")
    print(f"Time: {latest_article['timestamp']}")
    print(f"ID: {latest_article['id']}")
    
    # Check if this article has already been sent
    last_sent_id = get_latest_sent_id(bucket_name)
    if last_sent_id == latest_article['id']:
        print("Article already sent to Slack, skipping")
        return True
        
    # Send to Slack and save the ID if successful
    if send_to_slack(slack_webhook_url, latest_article):
        # Only save the ID if we successfully sent to Slack
        return save_latest_sent_id(bucket_name, latest_article['id'])
    
    return False

# For local testing
if __name__ == "__main__":
    check_new_listings(None, None)