import io
import os
import sys
import boto3
from datetime import datetime


EXTENSION_TO_CONTENT_TYPES = {
    "json": "application/json",
    "png": "image/png",
    "jpeg": "image/jpeg",
    "jpg": "image/jpeg",
    "mp4": "video/mp4",
    "html": "text/html",
    "txt": "text/plain"
}


def s3_put(location: str, stream: io.BytesIO):
    extension = location.split(".")[-1]
    return boto3.client(
        "s3",
        region_name=os.environ["AWS_DEFAULT_REGION"],
        aws_access_key_id=os.environ["AWS_ACCESS_KEY_ID"],
        aws_secret_access_key=os.environ["AWS_SECRET_ACCESS_KEY"],
    ).put_object(
        Bucket=os.environ["AWS_S3_BUCKET_NAME"],
        Body=stream,
        Key=location,
        ContentType=EXTENSION_TO_CONTENT_TYPES[extension]
    )


if __name__ == "__main__":
    if sys.argv[-1] == "test":
        print("Uploading:", "wikistatic/test.txt")
        s3_put("wikistatic/test.txt", str(datetime.now()).encode())
    else:
        for champion_filename in os.listdir("champions"):
            with open("champions/" + champion_filename, "rb") as f:
                print("Uploading:", champion_filename)
                s3_put(f"wikistatic/lol/resources/latest/en-US/champions/{champion_filename}", f)
        for item_filename in os.listdir("items"):
            with open("items/" + item_filename, "rb") as f:
                print("Uploading:", item_filename)
                s3_put(f"wikistatic/lol/resources/latest/en-US/items/{item_filename}", f)
