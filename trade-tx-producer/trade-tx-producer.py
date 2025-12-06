#!/usr/bin/env python3

import logging
from kafka import KafkaProducer
from aws_msk_iam_sasl_signer import MSKAuthTokenProvider
import json
import time
import os
import random
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Suppress verbose Kafka logs
logging.getLogger('kafka').setLevel(logging.WARNING)

# Configuration from environment variables
BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS")
REGION = os.getenv("AWS_REGION", "us-east-1")
TOPIC = os.getenv("KAFKA_TOPIC", "demo-topic")
MESSAGES_PER_SECOND = int(os.getenv("MESSAGES_PER_SECOND", 100))

# Print environment variables
# logger.info("Environment variables:")
# for key in sorted(os.environ.keys()):
#     logger.info(f"{key}: {os.environ[key]}")
# logger.info("=" * 50)

class TokenProvider:
    def __init__(self, region):
        self.region = region
    
    def token(self):
        token, _ = MSKAuthTokenProvider.generate_auth_token(self.region)
        return token

def create_producer():
    logger.info(f"Creating producer with bootstrap_servers: {BOOTSTRAP_SERVERS}")
    return KafkaProducer(
        bootstrap_servers=BOOTSTRAP_SERVERS,
        security_protocol='SASL_SSL',
        sasl_mechanism='OAUTHBEARER',
        sasl_oauth_token_provider=TokenProvider(REGION),
        value_serializer=lambda v: json.dumps(v).encode('utf-8'),
        api_version=(2, 5, 0)
    )

def generate_trade():
    account_id = f"ACC{random.randint(1000, 9999)}"
    symbols = ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA', 'META', 'NVDA']
    trade_types = ['BUY', 'SELL']
    
    return {
        "account_id": account_id,
        "trade_id": f"TRD{random.randint(100000, 999999)}",
        "symbol": random.choice(symbols),
        "trade_type": random.choice(trade_types),
        "quantity": random.randint(1, 1000),
        "price": round(random.uniform(50, 500), 2),
        "timestamp": datetime.utcnow().isoformat()
    }, account_id

def send_messages_continuously():
    producer = create_producer()
    count = 0
    
    if MESSAGES_PER_SECOND == 0:
        logger.info("Producer paused: MESSAGES_PER_SECOND=0 (not sending messages)")
        try:
            while True:
                time.sleep(60)
        except KeyboardInterrupt:
            logger.info("Stopping producer.")
        return
    
    delay = 1.0 / MESSAGES_PER_SECOND
    logger.info(f"Starting continuous producer: {MESSAGES_PER_SECOND} messages/second")
    logger.info(f"Delay between messages: {delay:.4f} seconds")
    
    try:
        while True:
            trade, account_id = generate_trade()
            producer.send(TOPIC, key=account_id.encode('utf-8'), value=trade)
            count += 1
            
            if count % 100 == 0:
                logger.info(f"Sent trades count: {count} - Last: {trade['trade_type']} {trade['quantity']} {trade['symbol']} for {account_id}")
            
            time.sleep(delay)
    except KeyboardInterrupt:
        logger.info(f"Stopping producer. Total messages sent: {count}")
    finally:
        producer.flush()
        producer.close()

if __name__ == "__main__":
    send_messages_continuously()
