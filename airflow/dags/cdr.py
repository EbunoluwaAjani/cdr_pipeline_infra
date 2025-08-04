import random
import string
import datetime
import logging
import pandas as pd
import awswrangler as wr
import boto3
from faker import Faker
from airflow.models import Variable

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

aws_access_key = Variable.get("AWS_ACCESS_KEY_ID")
aws_secret_key = Variable.get("AWS_SECRET_ACCESS_KEY")
aws_region = "eu-west-1"


fake = Faker('en_US')


def generate_random_phone():
    """Generates a random 13-digit phone number."""
    return "234" + "".join(random.choices(string.digits, k=10))


def generate_random_imei():
    """Generates a random 15-digit IMEI."""
    return "".join(random.choices(string.digits, k=15))


def load_to_s3(s3_path, num_records=None):
    """
    Generates synthetic CDR data and uploads it to S3 as a Parquet file.

    Args:
        s3_path (str): The S3 path to upload the data to.
        num_records (int): The number of synthetic records to generate.
    """
    if num_records is None:
        num_records = random.randint(100, 500)
    logging.info(f"Loading {num_records} records to {s3_path}")

    call_types = ["voice", "sms", "data"]
    networks = ["MTN", "Airtel", "Glo", "9mobile"]
    reasons = ["normal", "promo", "roaming"]
    billing_types = ["prepaid", "postpaid"]
    promo_codes = ["", "PROMO10", "SUMMER50", "FREECALL"]
    locations = ["Lagos", "Abuja", "Kano", "PH", "Ibadan"]
    bts = ["BTS001", "BTS002", "BTS003", "BTS004"]
    connection_statuses = ["connected", "disconnected", "failed"]
    service_plans = ["Basic", "Premium", "Business"]

    cdr_list = []

    for _ in range(num_records):
        call_start = (
            datetime.datetime.now()
            - datetime.timedelta(minutes=random.randint(1, 10000))
        )
        duration = random.randint(1, 3600)
        call_end = call_start + datetime.timedelta(seconds=duration)

        call_quality = round(random.uniform(1.0, 5.0), 2)
        cost = round(duration * random.uniform(0.01, 0.05), 2)
        balance = round(random.uniform(0, 5000), 2)
        charged = random.choice([True, False])
        data_usage = round(random.uniform(0.1, 500), 2)

        cdr_list.append({
            "caller_number": generate_random_phone(),
            "receiver_number": generate_random_phone(),
            "caller_imei": generate_random_imei(),
            "receiver_imei": generate_random_imei(),
            "caller_location_bts": random.choice(bts),
            "receiver_location_bts": random.choice(bts),
            "tower_id": "TWR" + str(random.randint(100, 999)),
            "caller_network": random.choice(networks),
            "receiver_network": random.choice(networks),
            "roaming_status": random.choice(["local", "roaming"]),
            "call_quality": call_quality,
            "call_start": call_start,
            "call_end": call_end,
            "duration_seconds": duration,  # Renamed to match the new schema
            "call_type": random.choice(call_types),
            "location": random.choice(locations),
            "is_charged": charged,
            "charge_reason": random.choice(reasons),
            "billing_type": random.choice(billing_types),
            "promo_code": random.choice(promo_codes),
            "account_balance": balance,
            "cost": cost,
            "data_usage_mb": data_usage,
            "connection_status": random.choice(connection_statuses),
            "service_plan": random.choice(service_plans)
        })
    df = pd.DataFrame(cdr_list)

    df['caller_number'] = df['caller_number'].astype(str)
    df['receiver_number'] = df['receiver_number'].astype(str)
    df['caller_imei'] = df['caller_imei'].astype(str)
    df['receiver_imei'] = df['receiver_imei'].astype(str)
    df['caller_location_bts'] = df['caller_location_bts'].astype(str)
    df['receiver_location_bts'] = df['receiver_location_bts'].astype(str)
    df['tower_id'] = df['tower_id'].astype(str)
    df['caller_network'] = df['caller_network'].astype(str)
    df['receiver_network'] = df['receiver_network'].astype(str)
    df['roaming_status'] = df['roaming_status'].astype(str)
    df['call_quality'] = df['call_quality'].astype(float)
    df['call_start'] = pd.to_datetime(df['call_start'])
    df['call_end'] = pd.to_datetime(df['call_end'])
    df['duration_seconds'] = df['duration_seconds'].astype(int)
    df['call_type'] = df['call_type'].astype(str)
    df['location'] = df['location'].astype(str)
    df['is_charged'] = df['is_charged'].astype(bool)
    df['charge_reason'] = df['charge_reason'].astype(str)
    df['billing_type'] = df['billing_type'].astype(str)
    df['promo_code'] = df['promo_code'].fillna('').astype(str)
    df['account_balance'] = df['account_balance'].astype(float)
    df['cost'] = df['cost'].astype(float)
    df['data_usage_mb'] = df['data_usage_mb'].astype(float)
    df['connection_status'] = df['connection_status'].astype(str)
    df['service_plan'] = df['service_plan'].astype(str)

    if df.empty:
        logging.warning("DataFrame is empty. Skipping S3 upload.")
        return
    # --- Generate File Name and Path ---
    ingestion_date = datetime.datetime.now().strftime("%Y-%m-%d")
    full_s3_path = f"{s3_path}/cdr_{ingestion_date}.parquet/"

    # --- AWS Session ---
    session = boto3.Session(
        aws_access_key_id=aws_access_key,
        aws_secret_access_key=aws_secret_key,
        region_name=aws_region
    )

    # --- Upload to S3 ---
    wr.s3.to_parquet(
        df=df,
        path=full_s3_path,
        boto3_session=session,
        dataset=True,
        mode='append'
    )

    logging.info(f"Uploaded {len(df)} records to {full_s3_path}")
