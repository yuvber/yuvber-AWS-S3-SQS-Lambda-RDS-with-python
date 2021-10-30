import boto3
import os

buckets_list = []
MAX_USERNAME_LEN = 20
MIN_USERNAME_LEN = 2
region = 'us-east-1'


# to know if a user already have an environment we will check if his bucket exists
def is_user_exist(username):
    s3 = boto3.resource('s3')
    for bucket in s3.buckets.all():  # pulling out bucket names
        buckets_list.append(bucket.name)

    if f"{username}-bucket" in buckets_list:
        return True
    else:
        return False


def creating_bucket(username):
    s3_client = boto3.client('s3')
    boto3.resource('s3')

    s3_client.create_bucket(Bucket=f"{username}-bucket")  # creating a new bucket


# uploading the lambda code into the user`s bucket
# user needs to provide file path
def uploading_lambda_file(lambda_file_path, username):
    s3_client = boto3.client('s3')
    s3_client.upload_file(lambda_file_path, f"{username}-bucket", 'lambda_function.py')  # uploading a new file to the bucket


# uploading a new file to the bucket
# user needs to provide file path
def uploading_file(file_path, username, file_number):
    try:  # checking if file path is valid
        s3_client = boto3.client('s3')
        s3_client.upload_file(file_path, f"{username}-bucket", f"{username}-file{file_number}")
        return True
    except Exception:
        print("Unable to upload the file please check the path you provided...")
        return False


def delete_bucket(username):
    s3 = boto3.resource('s3')
    bucket = s3.Bucket(f"{username}-bucket")
    bucket.objects.all().delete()  # deleting all files
    bucket.delete()  # deleting the bucket


# creating a new queue
def create_queue(username):
    # Get the service resource
    sqs = boto3.resource('sqs', region_name='us-east-1')

    # Create the queue. This returns an SQS.Queue instance
    sqs.create_queue(QueueName=f"{username}-queue", Attributes={'DelaySeconds': '5'})


# send messages to the queue
def send_message(username, file_number):
    file_number = file_number - 1  # matching the file num in the message to the one in the bucket
    sqs = boto3.resource('sqs', region_name='us-east-1')

    # Get the queue
    queue = sqs.get_queue_by_name(QueueName=f"{username}-queue")

    # Create a new message
    # massage contains bucket and file name for the lambda function to process
    queue.send_message(MessageBody=f'{username},{file_number}')


def delete_queue(username, region):
    client = boto3.client("sts", region_name=region)

    account_id = client.get_caller_identity()["Account"]  # getting the account id
    client = boto3.client('sqs', region_name=region)

    queue_url = client.get_queue_url(  # getting the queue url using account id
        QueueName=f"{username}-queue",
        QueueOwnerAWSAccountId=account_id)

    client = boto3.client('sqs', region_name=region)
    client.delete_queue(QueueUrl=queue_url['QueueUrl'])  # deleting queue using queue url


def create_lambda_function(username, region):
    client = boto3.client('lambda', region_name=region)
    # creating the lambda function
    client.create_function(
        FunctionName=f'{username}_function',
        Runtime='python3.8',
        Timeout=30,
        Role='arn:aws:iam::399308550545:role/new_role2',
        Handler="lambda_function.lambda_handler",
        Code={
            'S3Bucket': f"{username}-bucket",
            'S3Key': 'lambda_function.py'
        }
    )
    # making the queue we created the lambda trigger
    client.create_event_source_mapping(
        BatchSize=5,
        EventSourceArn=f'arn:aws:sqs:us-east-1:399308550545:{username}-queue',
        FunctionName=f'{username}_function',
    )


def delete_lambda_function(username, region):
    client = boto3.client('lambda', region_name=region)
    client.delete_function(FunctionName=f'{username}_function')


def create_database(username, region):
    client = boto3.client('rds', region_name=region)
    client.create_db_instance(
        DBName=f'{username}DB',
        DBInstanceIdentifier=f'{username}-instance',
        AllocatedStorage=20,
        DBInstanceClass='db.t2.micro',
        Engine='mysql',
        MasterUsername='admin',
        MasterUserPassword='password',
        VpcSecurityGroupIds=[
            'sg-02c1bc3361553a05f',
        ],
        AvailabilityZone='us-east-1a',
        BackupRetentionPeriod=0,
        Port=3306,
        PubliclyAccessible=True,
        StorageType='standard',
    )


def delete_database(username, region):

    client = boto3.client('rds', region_name=region)
    client.delete_db_instance(
        DBInstanceIdentifier=f'{username}-instance',
        SkipFinalSnapshot=True,
        DeleteAutomatedBackups=True
    )


def check_aws_validity(key_id, secret):
    try:
        client = boto3.client('s3', aws_access_key_id=key_id, aws_secret_access_key=secret)
        client.list_buckets()
        return True

    except Exception as e:
        if str(e) != "An error occurred (InvalidAccessKeyId) when calling the ListBuckets" \
                     " operation: The AWS Access Key Id you provided does not exist in our records.":
            return False
        return False


def main_menu():

    lambda_file_path = input('enter the lambda zip file path you got: ')
    region = 'us-east-1'
    file_number = 1
    create_env = 0
    delete_env = 0
    NEW_ENV = '1'
    UPLOAD_FILE = '2'
    DELETE_ENV = '3'
    EXIT = '4'

    while True:  # making sure that user name is valid and does not exist already
        user_name = str(input("Please enter your user name: "))
        if MIN_USERNAME_LEN < len(user_name) < MAX_USERNAME_LEN and user_name.isalnum():
            if not is_user_exist(user_name):
                print(f"Welcome {user_name}!")
                break
            else:
                print('user name already exists')

        else:
            print("Invalid user_name (must be alphanumeric and between 3-20 characters long)")

    while True:
        # asking user for input (his name and credentials)
        # get the user name and the key for aws and make it an environment variable

        print("1. Create new enviorment")
        print("2. Upload file")
        print("3. Delete enviorment")
        print("4. Exit")
        choice = input("Please select an option: ")

        if choice == NEW_ENV:
            while True:  # checking whether the user already created an environment
                if is_user_exist(user_name):
                    print('you already have one environment')
                    print('please choose another option')
                    break
                else:
                    creating_bucket(user_name)
                    uploading_lambda_file(lambda_file_path, user_name)
                    create_queue(user_name)
                    create_lambda_function(user_name, region)
                    create_database(user_name, region)
                    create_env = 1
                    print('congrats! you have an environment')
                    break
        elif choice == UPLOAD_FILE:
            if create_env != 1:
                print('you have to create an environment in order to upload a file')
                continue

            file_path = input('enter the file path you want to upload ')
            if uploading_file(file_path, user_name, file_number):  # checking if uploading file raise an error
                file_number += 1  # making sure that the file names are different
                send_message(user_name, file_number)
                print('your file is uploaded and in your S3 bucket. the file '
                      'content is in the mysql database')

        elif choice == DELETE_ENV:
            if create_env != 1:  # checking if user has an environment
                print('you have to create an environment in order to delete it')
                continue
            delete_env += 1
            if delete_env != 1:
                print('you already deleted your environment')
                print('select another option please')
                continue

            delete_bucket(user_name)
            delete_queue(user_name, region)
            delete_lambda_function(user_name, region)
            delete_database(user_name, region)
            print('your environment has been deleted successfully')
        elif choice == EXIT:
            print("Goodbye!")
            exit()
        else:
            print("Invalid Choice\ntry again...")


def main():

    while True:
        user_aws_access_key_id = input('enter the aws_access_key_id please: ')
        user_aws_secret_access_key = input('enter the aws_secret_access_key: ')
        os.environ['AWS_ACCESS_KEY_ID'] = user_aws_access_key_id
        os.environ['AWS_SECRET_ACCESS_KEY'] = user_aws_secret_access_key
        os.environ['AWS_REGION'] = 'us-east-1'

        if check_aws_validity(user_aws_access_key_id, user_aws_secret_access_key):
            main_menu()
        else:
            print("Invalid credentials please try again...")


if __name__ == '__main__':
    main()


