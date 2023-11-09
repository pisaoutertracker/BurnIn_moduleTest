#!/bin/bash

curl -X GET -H "Content-Type: application/json" "http://192.168.0.45:5000/modules"

curl -X GET -H "Content-Type: application/json" "http://192.168.0.45:5000/tests"

# Define the API endpoint URL and module ID
API_URL="http://192.168.0.45:5000/tests"

# Define the data to update as a JSON string
UPDATED_MODULE='{
"testID": "T20231107135334326041", 
"modules_list": ["654a1486b8b38796342687cd", 
"654a1486b8b38796342687c4", 
"654a1486b8b38796342688cd", 
"654a1486b8b3879634268c39", 
"654a1486b8b387963426876a", 
"654a1486b8b3879634268ab6", 
"654a1486b8b38796342688e7", 
"654a1486b8b3879634268bd9", 
"654a1486b8b387963426887c", 
"654a1486b8b3879634268917"], 
"testType": "Type3", 
"testDate": "2006-08-29", 
"testOperator": "Thomas Ward", 
"testStatus": "ongoing", 
"testResults": {"result": "pass"}}
'

# Send a PUT request using curl
#curl -X POST -H "Content-Type: application/json" -d "$UPDATED_MODULE" "$API_URL"
