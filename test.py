import time

import requests
import json

URL = "http://localhost:5000/"

headers = {'content-type': 'application/json'}
requests_sleep = 10
tests_sleep = requests_sleep * 2
mock_json = """{
	"mock": [
		{
			"mock_id": "0"
		}gitg
	]
}"""

# Add a new scan
print(f"Dispatching {URL}new-scan three times")
new_scan_response1 = json.loads(
    requests.put(url=URL + "new-scan?sleeping-time=" + str(requests_sleep), data=mock_json, headers=headers).text)
print("New scan been added")
print(f'ID: {new_scan_response1["id"]} : {new_scan_response1["status"]}\n')
new_scan_response2 = json.loads(
    requests.put(url=URL + "new-scan?sleeping-time=" + str(requests_sleep), data=mock_json, headers=headers).text)
print("New scan been added")
print(f'ID: {new_scan_response2["id"]} : {new_scan_response2["status"]}\n')
new_scan_response3 = json.loads(
    requests.put(url=URL + "new-scan?sleeping-time=" + str(requests_sleep), data=mock_json, headers=headers).text)
print("New scan been added")
print(f'ID: {new_scan_response3["id"]} : {new_scan_response3["status"]}\n')

print("Three new scans been added, should be status Accepted\n")

# Check statuses
print(f"Dispatching {URL}status/[id] three times (Three created ids...)\n")
new_scan_response1 = json.loads(requests.get(URL + "status/" + str(new_scan_response1["id"])).content)
new_scan_response2 = json.loads(requests.get(URL + "status/" + str(new_scan_response2["id"])).content)
new_scan_response3 = json.loads(requests.get(URL + "status/" + str(new_scan_response3["id"])).content)

print("Now should be Running")
print("Statuses:")
print(f'ID: {new_scan_response1["id"]} : {new_scan_response1["status"]}')
print(f'ID: {new_scan_response2["id"]} : {new_scan_response1["status"]}')
print(f'ID: {new_scan_response3["id"]} : {new_scan_response1["status"]}\n')

print("Sleeping while scan works...\n")
# time.sleep(tests_sleep)

# Check statuses again
print(f"Dispatching {URL}status/[id] three times (Three created ids...)\n")
new_scan_response1 = json.loads(requests.get(URL + "status/" + str(new_scan_response1["id"])).content)
new_scan_response2 = json.loads(requests.get(URL + "status/" + str(new_scan_response2["id"])).content)
new_scan_response3 = json.loads(requests.get(URL + "status/" + str(new_scan_response3["id"])).content)

print("Now should be Complete")
print("Statuses:")
print(f'ID: {new_scan_response1["id"]} : {new_scan_response1["status"]}')
print(f'ID: {new_scan_response2["id"]} : {new_scan_response1["status"]}')
print(f'ID: {new_scan_response3["id"]} : {new_scan_response1["status"]}\n')

# Simulate error
print(f"Dispatching {URL}new-scan?simulate-error=True\n")
new_scan_response1 = json.loads(
    requests.put(URL + "new-scan?simulate-error=True&sleeping-time=" + str(requests_sleep), data=mock_json,
                 headers=headers).text)

print("Sleeping while scan works...\n")
time.sleep(tests_sleep)

new_scan_response1 = json.loads(requests.get(URL + "status/" + str(new_scan_response1["id"])).content)

print("Now should be Error")
print("Statuses:")
print(f'ID: {new_scan_response1["id"]} : {new_scan_response1["status"]}\n')

print("Trying to get status of a non-existing scan:\n")
new_scan_response1 = json.loads(requests.get(URL + "status/" + str(new_scan_response1["id"] + 1)).content)

print("Now should be Not-Found")
print("Statuses:")
print(f'ID: {new_scan_response1["id"]} : {new_scan_response1["status"]}\n')
