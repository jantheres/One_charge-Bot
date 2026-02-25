import requests, json, time

BASE = "https://web-production-cabb.up.railway.app"

print("=" * 55)
print("  FULL CHAT FLOW TEST")
print("=" * 55)

# Step 1: Login
print("\n--- STEP 1: Login ---")
r = requests.post(f"{BASE}/api/auth/login", json={"phone": "9876543210"}, timeout=10)
print(f"Status: {r.status_code}")
if r.status_code != 200:
    print(f"FAILED: {r.text}")
    exit()
token = r.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}
print("Token received!")

# Step 2: Start conversation
print("\n--- STEP 2: Start Chat ---")
r = requests.post(f"{BASE}/api/chatbot/start", headers=headers, timeout=15)
print(f"Status: {r.status_code}")
data = r.json()
print(f"Session: {data.get('session_id')}")
print(f"State: {data.get('state')}")
print(f"Message: {data.get('message', '')[:100]}...")
print(f"Options: {data.get('options')}")
session_id = data.get("session_id")

if not session_id:
    print("FAILED: No session_id")
    exit()

# Step 3: Send location
print("\n--- STEP 3: Send Location ---")
r = requests.post(f"{BASE}/api/chatbot/message", headers=headers, json={
    "session_id": session_id,
    "message": "I am near MG Road, Bangalore",
    "message_type": "text"
}, timeout=20)
print(f"Status: {r.status_code}")
data = r.json()
print(f"State: {data.get('state')}")
print(f"Message: {data.get('message', '')[:100]}...")
print(f"Options: {data.get('options')}")

# Step 4: Safety check
print("\n--- STEP 4: Safety Check ---")
r = requests.post(f"{BASE}/api/chatbot/message", headers=headers, json={
    "session_id": session_id,
    "message": "Yes I am safe",
    "message_type": "text"
}, timeout=20)
print(f"Status: {r.status_code}")
data = r.json()
print(f"State: {data.get('state')}")
print(f"Message: {data.get('message', '')[:100]}...")
print(f"Options: {data.get('options')}")

# Step 5: Issue type
print("\n--- STEP 5: Issue Type ---")
r = requests.post(f"{BASE}/api/chatbot/message", headers=headers, json={
    "session_id": session_id,
    "message": "Flat tyre",
    "message_type": "text"
}, timeout=20)
print(f"Status: {r.status_code}")
data = r.json()
print(f"State: {data.get('state')}")
print(f"Message: {data.get('message', '')[:100]}...")
print(f"Options: {data.get('options')}")

# Step 6: Service preference
print("\n--- STEP 6: Service Preference ---")
r = requests.post(f"{BASE}/api/chatbot/message", headers=headers, json={
    "session_id": session_id,
    "message": "On-spot repair please",
    "message_type": "text"
}, timeout=20)
print(f"Status: {r.status_code}")
data = r.json()
print(f"State: {data.get('state')}")
print(f"Message: {data.get('message', '')[:100]}...")
print(f"Request ID: {data.get('request_id')}")

print("\n" + "=" * 55)
print("  CHAT FLOW COMPLETE!")
print("=" * 55)
