import boto3
import re

import json
import sys
import logging
import pymysql


def lambda_handler(event, context):
    aws_access_key_id='AKIAVZ6FE6GIT7UC3OGS'
    aws_secret_access_key='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'
    
    username, file_number = event['Records'][0]["body"].split(',')
    
    db_port = 3306 
    db_username = "admin"
    db_password = "password"
    db_name = f"{username}DB"
    instance_name = f"{username}-instance"
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    try:
        rds = boto3.client('rds')
        instances = rds.describe_db_instances(DBInstanceIdentifier=instance_name) # acess user instance
        db_endpoint = instances.get('DBInstances')[0]['Endpoint']['Address'] # get endpoint address
        conn = pymysql.connect(host=db_endpoint, user=db_username, password=db_password, port=db_port, database=db_name, connect_timeout=5) # connecting to database
    except pymysql.MySQLError as e:
        logger.error(f"ERROR: Unexpected error: Could not connect to MySQL instance")
        logger.error(e)
        sys.exit()
    logger.info("SUCCESS: Connection to RDS MySQL instance succeeded")
    
    s3 = boto3.client('s3', aws_access_key_id=aws_access_key_id, aws_secret_access_key=aws_secret_access_key)
    json_file = s3.get_object(Bucket=f"{username}-bucket", Key=f"{username}-file{file_number}")['Body']  # getting file object without downloading it
    json_data = json.load(json_file) # coverting json to dict
    
    with conn.cursor() as cur:
        cur.execute("create table if not exists workers(id int key,name varchar(20) not null, company varchar(20) not null);")
        cur.execute(f"insert into `workers` (`id`,`name`,`company`) value ({json_data['id']!r},{json_data['name']!r},{json_data['company']!r});")
    conn.commit()

    sqs = boto3.client('sqs', region_name='us-east-1')
    response_queue = sqs.delete_message(
        QueueUrl=f'https://sqs.us-east-1.amazonaws.com/399308550545/{username}-queue',
        ReceiptHandle=event['Records'][0]['receiptHandle']
    )

    return {
        'statusCode': 200,
        'body': 'Done'
    }
