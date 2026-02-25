from botocore.exceptions import ClientError
from utils.file_tracker import get_file_list
from utils.credentials import init_s3_ilya

s3_client = init_s3_ilya()

def check_file_exists(bucket_name, key) -> bool:
    print(f"Checking if s3://{bucket_name}/{key} exists")
    try:
        s3_client.head_object(Bucket=bucket_name, Key=key)
        return True
    except ClientError as e:
        return False
    except Exception as e:
        print(e)
        return False

file_list = get_file_list()

def record_file(file_path):
    with open("exists.txt", 'a+') as f:
        f.write(file_path + "\n")

def log(text):
    print(text)
    with open("out-exists.txt", 'a+') as f:
        f.write(text + "\n")

count = 0
bucket = "taipale-lab-data-trasnfer"

for k, file in enumerate(file_list):
    if not file.endswith("/"):
        file = file.removeprefix("rcs-ajt208-server-mirror/")
        exists = check_file_exists(bucket, f"mirror/{file}")
        if exists:
            record_file(file)
            count+=1
        log(f"Checking {(k+1)/len(file_list)*100}%...\n\tFiles in tape server: \n\t\t{len(file_list)}\n\tFiles in s3://{bucket}/\n\t\t{count}\n\tOverlap: \n\t\t{count/len(file_list)*100}%")

