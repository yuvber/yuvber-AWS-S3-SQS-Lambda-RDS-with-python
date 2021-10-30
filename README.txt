Hello!
With this script you will be able to create yourself an AWS environment.
You will have S3 bucket, sqs queue, Lambda function and a mysql database, all naming after you
and private for your use only.
The lambda function will be executed every time you upload a file to the bucket (file must be in
a specific JSON format),
it will send the file content into mysql database table.

You also got with this folder a zip file,named lambda_function.zip.
Please insert its path when needed, it contains the lambda code
and some libraries it needs.

things you need to know:

1. the JSON file must be in a specific format and values. The program accepts one row at a time.
   here is an example of a file content
{
"id": 2,
"name": "yuval",
"company": "unemployed"
}

2. when a user create an environment he needs to wait until the database is created in RDS.
   usually takes around 3 minutes.

3. to enter the table in mysql workbench you will need username and password
   user name: admin
   password: password


you will also need credentials to enter the main menu.
The credentials will be your aws_access_key_id and aws_secret_access_key.

Have fun!!