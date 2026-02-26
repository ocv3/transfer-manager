import datetime

def log(text, tag="TRANSFER"):
    date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    text = f"{date} {tag}: {text}\n"

    with open(f"log.txt", "a+") as log:
        log.write(text)
    print(text, end="")