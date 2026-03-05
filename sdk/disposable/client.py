import requests
import sys

API = "http://130.51.23.85:8000/run"

def run(cmd):
    r = requests.post(API, json={"script": cmd})
    print(r.text)

def main():
    cmd = " ".join(sys.argv[1:])
    run(cmd)

if __name__ == "__main__":
    main()
