#from faker.config import AVAILABLE_LOCALES
#print(AVAILABLE_LOCALES)


import os
import random
from datetime import datetime, timedelta

import awswrangler as wr
import boto3
import pandas as pd
from dotenv import load_dotenv
from faker import Faker
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

load_dotenv()
aws_access_key = os.getenv("AWS_ACCESS_KEY_ID")
aws_secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")

# Initialize AWS session
session = boto3.Session(
    aws_access_key_id=aws_access_key,
    aws_secret_access_key=aws_secret_key,
    region_name="eu-west-1"
)

fake = Faker('ng_NG')

# Compute yesterday's date
today = datetime.now()
yesterday = today - timedelta(days=1)


def generate_cdr():
    seconds_into_day = random.randint(0, 86399)
    call_start = datetime.combine(yesterday.date(), datetime.min.time()) + timedelta(seconds=seconds_into_day)
    duration = random.randint(1, 3600)
    call_end = call_start + timedelta(seconds=duration)
    call_type = random.choice(['voice', 'SMS', 'data'])
    cost_per_second = {'voice': 0.11, 'SMS': 4.00, 'data': 0.05}
    is_charged = random.choice([True, False])
    charge_reason = random.choice([
        "Standard billing", "Promo applied", "Same-network free call",
        "Bonus airtime", "First minute free", "Call dropped early"
    ]) if not is_charged else "Standard billing"
    cost = round(duration * cost_per_second[call_type], 2) if is_charged else 0.0

    return {
        "caller_number": fake.msisdn(),
        "receiver_number": fake.msisdn(),
        "caller_imei": fake.ean(length=13),
        "receiver_imei": fake.ean(length=13),
        "caller_location_bts": f"BTS-{random.randint(1000, 9999)}",
        "receiver_location_bts": f"BTS-{random.randint(1000, 9999)}",
        "tower_id": f"BTS-{random.randint(1000, 9999)}",
        "caller_network": random.choice(['MTN', 'Airtel', 'Glo', '9mobile']),
        "receiver_network": random.choice(['MTN', 'Airtel', 'Glo', '9mobile']),
        "roaming_status": random.choice(['local', 'roaming']),
        "call_quality": round(random.uniform(2.5, 5.0), 2),
        "call_start": call_start.isoformat(),
        "call_end": call_end.isoformat(),
        "duration": duration,
        "call_type": call_type,
        "location": fake.city(),
        "is_charged": is_charged,
        "charge_reason": charge_reason,
        "billing_type": random.choice(['prepaid', 'postpaid']),
        "promo_code": fake.bothify(text='PROMO-####??'),
        "account_balance": round(random.uniform(0, 5000), 2),
        "cost": cost
    }


def load_to_s3(s3_path: str):
    cdrs = [generate_cdr() for _ in range(100)]
    df = pd.DataFrame(cdrs)
    if df.empty:
        logging.warning("DataFrame is empty. Skipping S3 upload.")
        return
    ingestion_date = datetime.now().strftime("%Y-%m-%d")
    file_name = f"cdr_{ingestion_date}.parquet"
    full_s3_path = f"{s3_path}/{file_name}"

    wr.s3.to_parquet(
        df=df,
        path=full_s3_path,
        boto3_session=session,
        dataset=True,
        mode="append"
    )
    logging.info("Data successfully written to S3 at %s", full_s3_path)
    print(f"Done! {len(df):,} transaction records written to {full_s3_path}")


# Call the function
s3_path = "s3://test-bucket-0008789"
load_to_s3(s3_path)

