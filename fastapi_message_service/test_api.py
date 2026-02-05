import requests
import json
import time
import uuid

URL = "http://127.0.0.1:8001/message"

HEADERS = {
    "x-api-key": "kr7-secret",
    "Content-Type": "application/json"
}


def run_test(message, description):
    print(f"\n=== {description} ===")

    cid = str(uuid.uuid4())   # ⭐ fresh conversation every test

    payload = {
        "conversation_id": cid,
        "message": message
    }

    try:
        response = requests.post(URL, json=payload, headers=HEADERS)

        print(f"Status Code: {response.status_code}")

        try:
            print(json.dumps(response.json(), indent=2))
        except:
            print(response.text)

    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")


if __name__ == "__main__":

    # Normal message
    run_test(
        "Hello, this is a legitimate message.",
        "Test 1: Normal Message"
    )
    time.sleep(2)

    # Scam message (agent reply)
    run_test(
        "Please share otp for verification.",
        "Test 2: Scam Detection + Agent"
    )
    time.sleep(2)

    # Extraction test (UPI + URL + Account)
    run_test(
        "Send money to test@upi and use account 12345678901 and visit http://fake.com",
        "Test 3: Intelligence Extraction"
    )
