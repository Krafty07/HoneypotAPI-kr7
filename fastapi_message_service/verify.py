import urllib.request
import urllib.error
import json
import sys
import time

url = "http://127.0.0.1:8001/message"
headers = {
    "Content-Type": "application/json",
    "x-api-key": "kr7-secret"
}
# Health check with distinct ID
health_data = json.dumps({"conversation_id": "health_check", "message": "ping"}).encode('utf-8')

print("Waiting for server to be ready...")
for i in range(10):
    try:
        req = urllib.request.Request(url, data=health_data, headers=headers, method="POST")
        with urllib.request.urlopen(req) as response:
            pass
        print("Server is ready.")
        break
    except urllib.error.URLError:
        time.sleep(1)
    except urllib.error.HTTPError:
        print("Server is ready (responded with error, but port is open).")
        break
else:
    print("Server failed to start.")
    sys.exit(1)

# Generate unique ID for tests to avoid state collision
import random
test_conv_id = f"test_conv_{random.randint(1000, 9999)}"
data = json.dumps({"conversation_id": test_conv_id, "message": "hello"}).encode('utf-8')

# Test 1: Valid request
print(f"\nRunning Test 1: Valid Request (ID: {test_conv_id})")
req = urllib.request.Request(url, data=data, headers=headers, method="POST")
try:
    with urllib.request.urlopen(req) as response:
        if response.status != 200:
            print(f"Test 1 Failed: Status {response.status}")
            sys.exit(1)
        res_json = json.loads(response.read().decode())
        print(f"Test 1 Response: {res_json}")
        if res_json['turns'] != 1:
            # Note: If this test runs multiple times within the same server session, turns might be > 1.
            # We accept >= 1 for robustness or assume fresh start. 
            # Since we just started server, should be 1.
            print(f"Test 1 Failed: Expected turns=1, got {res_json['turns']}")
            sys.exit(1)
except Exception as e:
    print(f"Test 1 Error: {e}")
    sys.exit(1)

# Test 2: Increment turns
print("\nRunning Test 2: Increment Turns")
req = urllib.request.Request(url, data=data, headers=headers, method="POST")
try:
    with urllib.request.urlopen(req) as response:
        res_json = json.loads(response.read().decode())
        print(f"Test 2 Response: {res_json}")
        if res_json['turns'] != 2:
            print(f"Test 2 Failed: Expected turns=2, got {res_json['turns']}")
            sys.exit(1)
except Exception as e:
    print(f"Test 2 Error: {e}")
    sys.exit(1)

# Test 3: Auth failure
print("\nRunning Test 3: Auth Failure")
headers_invalid = headers.copy()
headers_invalid["x-api-key"] = "wrong-key"
req = urllib.request.Request(url, data=data, headers=headers_invalid, method="POST")
try:
    with urllib.request.urlopen(req) as response:
        print(f"Test 3 Failed: Should satisfy 401, got {response.status}")
        sys.exit(1)
except urllib.error.HTTPError as e:
    if e.code == 401:
        print("Test 3 Passed: Got 401 as expected")
    else:
        print(f"Test 3 Failed: Got {e.code}, expected 401")
        sys.exit(1)
except Exception as e:
    print(f"Test 3 Error: {e}")
    sys.exit(1)

print("\nAll tests passed!")
