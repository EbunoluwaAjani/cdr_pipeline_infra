import logging

import boto3
import pymysql
import requests
from airflow.models import Variable

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


def load_users_to_rds(
    rds_instance_id='dev-rds-instance',
    db_name='dev_db',
    aws_region='eu-west-1',
    user_count=500
):
    aws_access_key = Variable.get("AWS_ACCESS_KEY_ID")
    aws_secret_key = Variable.get("AWS_SECRET_ACCESS_KEY")
    user_param = Variable.get("RDS_SSM_USER_PARAM")
    password_param = Variable.get("RDS_SSM_PASSWORD_PARAM")

    session = boto3.Session(
        aws_access_key_id=aws_access_key,
        aws_secret_access_key=aws_secret_key,
        region_name=aws_region
    )

    rds = session.client("rds")
    db_instance = rds.describe_db_instances(
        DBInstanceIdentifier=rds_instance_id
    )['DBInstances'][0]
    endpoint = db_instance['Endpoint']['Address']
    port = db_instance['Endpoint']['Port']

    ssm = session.client('ssm')
    rds_username = ssm.get_parameter(
        Name=user_param, WithDecryption=True
    )['Parameter']['Value']
    rds_password = ssm.get_parameter(
        Name=password_param, WithDecryption=True
    )['Parameter']['Value']

    conn = pymysql.connect(
        host=endpoint,
        user=rds_username,
        password=rds_password,
        database=db_name,
        port=port
    )

    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                first_name VARCHAR(100),
                last_name VARCHAR(100),
                email VARCHAR(255)
            );
            """
        )

        response = requests.get(
            f"https://randomuser.me/api/?results={user_count}"
        )

        if response.status_code == 200:
            users = response.json()['results']
            for user in users:
                cursor.execute(
                    (
                        "INSERT INTO users (first_name, last_name, email) "
                        "VALUES (%s, %s, %s)"
                    ),
                    (
                        user['name']['first'],
                        user['name']['last'],
                        user['email']
                    )
                )
            conn.commit()
            logger.info("%d users loaded successfully.", len(users))
        else:
            logger.error("Failed to fetch users: %s", response.status_code)

    except Exception as e:
        logger.exception("Error during user load process: %s", str(e))

    finally:
        cursor.close()
        conn.close()
