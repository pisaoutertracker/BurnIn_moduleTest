#!/bin/bash

curl -X GET -H "Content-Type: application/json" "http://192.168.0.45:5000/modules"

curl -X GET -H "Content-Type: application/json" "http://192.168.0.45:5000/tests"

# Define the API endpoint URL and module ID
API_URL="http://192.168.0.45:5000/tests"

# Define the data to update as a JSON string
UPDATED_MODULE="{
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
"

UPDATED_TEST='{"modules_list": ["655f83caf1b4601dba648ad3"],
 "outputFile": "/T2023_11_23_17_55_39_286168/output_mqdms.zip",
 "runFolder": "T2023_11_23_17_55_39_286168",
 "testDate": "2023-11-23 17:55:39.286168",
 "testID": "T2023_11_23_17_55_39_286168",
 "testOperator": "Mickey Mouse",
 "testResults": {"boards": {"0": "fc7ot3:50001"},
                 "noisePerChip": {"D_B(0)_O(0)_H(0)_NoiseDistribution_Chip(0)SSA": 3.996109875043233,
                                  "D_B(0)_O(0)_H(0)_NoiseDistribution_Chip(1)SSA": 3.8985653936862947,
                                  "D_B(0)_O(0)_H(0)_NoiseDistribution_Chip(10)MPA": 2.5679106665891593,
                                  "D_B(0)_O(0)_H(0)_NoiseDistribution_Chip(11)MPA": 2.5080498771121102,
                                  "D_B(0)_O(0)_H(0)_NoiseDistribution_Chip(12)MPA": 2.4380561017120876,
                                  "D_B(0)_O(0)_H(0)_NoiseDistribution_Chip(13)MPA": 2.4142314951245982,
                                  "D_B(0)_O(0)_H(0)_NoiseDistribution_Chip(14)MPA": 2.457911626373728,
                                  "D_B(0)_O(0)_H(0)_NoiseDistribution_Chip(15)MPA": 2.454197027968864,
                                  "D_B(0)_O(0)_H(0)_NoiseDistribution_Chip(2)SSA": 3.870311141014099,
                                  "D_B(0)_O(0)_H(0)_NoiseDistribution_Chip(3)SSA": 3.8381631871064505,
                                  "D_B(0)_O(0)_H(0)_NoiseDistribution_Chip(4)SSA": 3.63644570906957,
                                  "D_B(0)_O(0)_H(0)_NoiseDistribution_Chip(5)SSA": 3.6734722197055816,
                                  "D_B(0)_O(0)_H(0)_NoiseDistribution_Chip(6)SSA": 3.5184952477614084,
                                  "D_B(0)_O(0)_H(0)_NoiseDistribution_Chip(7)SSA": 3.4797366042931874,
                                  "D_B(0)_O(0)_H(0)_NoiseDistribution_Chip(8)MPA": 2.6226339942775665,
                                  "D_B(0)_O(0)_H(0)_NoiseDistribution_Chip(9)MPA": 2.6010414162029822,
                                  "D_B(0)_O(0)_H(1)_NoiseDistribution_Chip(0)SSA": 3.8541426638762157,
                                  "D_B(0)_O(0)_H(1)_NoiseDistribution_Chip(1)SSA": 3.699337476491928,
                                  "D_B(0)_O(0)_H(1)_NoiseDistribution_Chip(10)MPA": 2.334916250780225,
                                  "D_B(0)_O(0)_H(1)_NoiseDistribution_Chip(11)MPA": 2.34288176416109,
                                  "D_B(0)_O(0)_H(1)_NoiseDistribution_Chip(12)MPA": 2.3738041723767918,
                                  "D_B(0)_O(0)_H(1)_NoiseDistribution_Chip(13)MPA": 2.3189230604097246,
                                  "D_B(0)_O(0)_H(1)_NoiseDistribution_Chip(14)MPA": 2.3415415092060963,
                                  "D_B(0)_O(0)_H(1)_NoiseDistribution_Chip(15)MPA": 2.4326853587602577,
                                  "D_B(0)_O(0)_H(1)_NoiseDistribution_Chip(2)SSA": 3.6841865102450053,
                                  "D_B(0)_O(0)_H(1)_NoiseDistribution_Chip(3)SSA": 3.8385616381963095,
                                  "D_B(0)_O(0)_H(1)_NoiseDistribution_Chip(4)SSA": 4.0126207828521725,
                                  "D_B(0)_O(0)_H(1)_NoiseDistribution_Chip(5)SSA": 4.079845084746679,
                                  "D_B(0)_O(0)_H(1)_NoiseDistribution_Chip(6)SSA": 4.264101626475652,
                                  "D_B(0)_O(0)_H(1)_NoiseDistribution_Chip(7)SSA": 4.648258860905965,
                                  "D_B(0)_O(0)_H(1)_NoiseDistribution_Chip(8)MPA": 2.376675664198895,
                                  "D_B(0)_O(0)_H(1)_NoiseDistribution_Chip(9)MPA": 2.323539824721714},
                 "result": "pass",
                 "temperatures": ["1.2", "4.5"],
                 "xmlConfig": {"boards": {"0": {"ip": "fc7ot3:50001",
                                              "opticalGroups": {"0": {"hybrids": {"0": {"pixels": "range(8, 16)",
                                                                                    "strips": "range(0, 8)"},
                                                                                "1": {"pixels": "range(8, 16)",
                                                                                    "strips": "range(0, 8)"}},
                                                                    "lpGBT": "lpGBT_v1.txt"}}}},
                               "commonSettings": "pippo"},}'


# Send a PUT request using curl
curl -X POST -H "Content-Type: application/json" -d "$UPDATED_TEST" "$API_URL"
#curl -X POST -H "Content-Type: application/json" -d "$UPDATED_MODULE" "$API_URL"
