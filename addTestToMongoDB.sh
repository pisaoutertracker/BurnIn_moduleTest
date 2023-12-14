#!/bin/bash

API_URL="http://192.168.0.45:5000/test_run"

curl -X GET -H "Content-Type: application/json" $API_URL

API_URL="http://192.168.0.45:5000/addRun"

# Define the data to update as a JSON string
##Perugia 102
TEST_RUN="{
        'runDate': '1996-11-21',
        'runID': 'T52',
        'runOperator': 'Kristin Jackson',
        'runStatus': 'failed',
        'runType': 'Type1',
        'runBoards': {
            3: 'fc7ot2',
            4: 'fc7ot3',
        },
        'runModules' : { ## (board, optical group) : (moduleID, hwIDmodule)
            'fc7ot2_optical0' : ('M123', 67),
            'fc7ot2_optical1' : ('M124', 68),
            'fc7ot3_optical2' : ('M125', 69),
        },
        'runResults' : {
            67 : 'pass',
            68 : 'failed',
            69 : 'failed',
        },
        'runNoise' : {
            67 : {
                'SSA0': 4.348,
                'SSA4': 3.348,
                'MPA9': 2.348,
            },
            68 : {
                'SSA0': 3.348,
                'SSA1': 3.648,
            },
            69 : {
                'SSA0': 3.548,
                'SSA4': 3.248,
            }
        },
        'runConfiguration' : {'a':'b'},
        'runROOTFile' : 'link'
        }
"

echo curl -X POST -H "Content-Type: application/json" -d "$TEST_RUN" "$API_URL"

curl -X POST -H "Content-Type: application/json" -d "$TEST_RUN" "$API_URL"

