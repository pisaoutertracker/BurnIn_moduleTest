#from moduleTest import verbose, ip, port, lpGBTids
#from pprint import pprint


### upload the test result to the "tests" DB

import requests
ip="192.168.0.45"
port=5000
#port=5005

test_run_dataA = {'runDate': '2023-12-12T10:12:23.1112', 'runDate': '2023-12-12T11:23:12','runStatus': 'dAAAone', 'runType': 'Type1', 'runBoards': {0: 'fc7ot2'}, 'runModules': {'fc7ot2_optical2': ('PS_26_05-IBA_00102', 2762808384)}, 'runNoise': {2762808384: {'H0_SSA0': 3.7207650383313497, 'H0_SSA1': 3.70428858200709, 'H0_SSA2': 3.6756444454193113, 'H0_SSA3': 3.6368053515752155, 'H0_SSA4': 3.657840915520986, 'H0_SSA5': 3.515361261367798, 'H0_SSA6': 3.5503181258837384, 'H0_SSA7': 3.416625440120697, 'H0_MPA8': 2.5446283177783093, 'H0_MPA9': 2.625446818582714, 'H0_MPA10': 2.506483563982571, 'H0_MPA11': 2.475390747449516, 'H0_MPA12': 2.5463442895251016, 'H0_MPA13': 2.4806182003075565, 'H0_MPA14': 2.6560127541733283, 'H0_MPA15': 2.6345912574596393, 'H1_SSA0': 3.3726783176263173, 'H1_SSA1': 3.346232604980469, 'H1_SSA2': 3.4091180086135866, 'H1_SSA3': 3.399280661344528, 'H1_SSA4': 3.411885545651118, 'H1_SSA5': 3.579738461971283, 'H1_SSA6': 3.573726809024811, 'H1_SSA7': 3.657718018690745, 'H1_MPA8': 2.7640798039113483, 'H1_MPA9': 2.739577845507301, 'H1_MPA10': 2.72567202996385, 'H1_MPA11': 2.72390631424884, 'H1_MPA12': 2.778999204064409, 'H1_MPA13': 2.634798581568369, 'H1_MPA14': 2.5579848426083722, 'H1_MPA15': 2.5966400764882565}}, 'runConfiguration': {'commonSettings': 'pippo', 'Nevents': '100', 'boards': {'0': {'ip': 'fc7ot2:50001', 'opticalGroups': {'2': {'lpGBT': 'lpGBT_v1.txt', 'hybrids': {'0': {'strips': [0, 1, 2, 3, 4, 5, 6, 7], 'pixels': [8, 9, 10, 11, 12, 13, 14, 15]}, '1': {'strips': [0, 1, 2, 3, 4, 5, 6, 7], 'pixels': [8, 9, 10, 11, 12, 13, 14, 15]}}}}}}}, 'runFile': '/T2023_12_12_17_16_58_053727/output_bkogt.zip'}



#test_run_data = {

#{




# 'runOperator': 'Kristin Jackson',


# 'runStatus': 'done',
# 'runType': 'Type1',

#}


# URL of the API endpoint for updating a module
api_url = "http://%s:%d/addRun"%(ip, port)

# Send a PUT request
response = requests.post(api_url, json=test_run_dataA)

# Check the response
if response.status_code == 201:
    print("Test created successfully")
else:
    print("Failed to update the module. Status code:", response.status_code)


##!/bin/bash

#API_URL="http://192.168.0.45:5000/test_run"

#curl -X GET -H "Content-Type: application/json" $API_URL

## Define the data to update as a JSON string
###Perugia 102
#TEST_RUN="{
#        'runDate': '1996-11-21',
#        'runID': 'T52',
#        'runOperator': 'Kristin Jackson',
#        'runStatus': 'failed',
#        'runType': 'Type1',
#        'runBoards': {
#            3: 'fc7ot2',
#            4: 'fc7ot3',
#        },
#        'runModules' : { ## (board, optical group) : (moduleID, hwIDmodule)
#            'fc7ot2_optical0' : ('M123', 67),
#            'fc7ot2_optical1' : ('M124', 68),
#            'fc7ot3_optical2' : ('M125', 69),
#        },
#        'runResults' : {
#            67 : 'pass',
#            68 : 'failed',
#            69 : 'failed',
#        },
#        'runNoise' : {
#            67 : {
#                'SSA0': 4.348,
#                'SSA4': 3.348,
#                'MPA9': 2.348,
#            },
#            68 : {
#                'SSA0': 3.348,
#                'SSA1': 3.648,
#            },
#            69 : {
#                'SSA0': 3.548,
#                'SSA4': 3.248,
#            }
#        },
#        'runConfiguration' : {'a':'b'},
#        'runROOTFile' : 'link'
#        }
#"

#echo curl -X POST -H "Content-Type: application/json" -d "$TEST_RUN" "$API_URL/addRun"

#curl -X POST -H "Content-Type: application/json" -d "$TEST_RUN" "$API_URL/addRun"

