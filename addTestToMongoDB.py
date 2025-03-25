#from moduleTest import verbose, ip, port, lpGBTids
#from pprint import pprint


### upload the test result to the "tests" DB

import requests
ip="192.168.0.45"
port=5000
#port=5005

test_run_dataA = {'runDate': '2023-12-12T10:12:23.1112', 'runDate': '2023-12-12T11:23:12','runStatus': 'dAAAone', 'runType': 'Type1', 'runBoards': {0: 'fc7ot2'}, 'runModules': {'fc7ot2_optical2': ('PS_26_05-IBA_00102', 2762808384)}, 'runNoise': {2762808384: {'H0_SSA0': 3.7207650383313497, 'H0_SSA1': 3.70428858200709, 'H0_SSA2': 3.6756444454193113, 'H0_SSA3': 3.6368053515752155, 'H0_SSA4': 3.657840915520986, 'H0_SSA5': 3.515361261367798, 'H0_SSA6': 3.5503181258837384, 'H0_SSA7': 3.416625440120697, 'H0_MPA8': 2.5446283177783093, 'H0_MPA9': 2.625446818582714, 'H0_MPA10': 2.506483563982571, 'H0_MPA11': 2.475390747449516, 'H0_MPA12': 2.5463442895251016, 'H0_MPA13': 2.4806182003075565, 'H0_MPA14': 2.6560127541733283, 'H0_MPA15': 2.6345912574596393, 'H1_SSA0': 3.3726783176263173, 'H1_SSA1': 3.346232604980469, 'H1_SSA2': 3.4091180086135866, 'H1_SSA3': 3.399280661344528, 'H1_SSA4': 3.411885545651118, 'H1_SSA5': 3.579738461971283, 'H1_SSA6': 3.573726809024811, 'H1_SSA7': 3.657718018690745, 'H1_MPA8': 2.7640798039113483, 'H1_MPA9': 2.739577845507301, 'H1_MPA10': 2.72567202996385, 'H1_MPA11': 2.72390631424884, 'H1_MPA12': 2.778999204064409, 'H1_MPA13': 2.634798581568369, 'H1_MPA14': 2.5579848426083722, 'H1_MPA15': 2.5966400764882565}}, 'runConfiguration': {'commonSettings': 'pippo', 'Nevents': '100', 'boards': {'0': {'ip': 'fc7ot2:50001', 'opticalGroups': {'2': {'lpGBT': 'lpGBT_v1.txt', 'hybrids': {'0': {'strips': [0, 1, 2, 3, 4, 5, 6, 7], 'pixels': [8, 9, 10, 11, 12, 13, 14, 15]}, '1': {'strips': [0, 1, 2, 3, 4, 5, 6, 7], 'pixels': [8, 9, 10, 11, 12, 13, 14, 15]}}}}}}}, 'runFile': '/T2023_12_12_17_16_58_053727/output_bkogt.zip'}


test = {'runDate': '2024-06-19T10:56:26', 'runSession': 'session80', 'runStatus': 'done', 'runType': 'Type1', 'runBoards': {0: 'fake'}, 'runModules': {'fake_optical0': ('PS_26_05-IBA_00102', 3962125297)}, 'runNoise': {3962125297: {'H0_SSA0': 1.6686748445034028, 'H0_SSA1': 1.642870126167933, 'H0_SSA2': 1.8782315522432327, 'H0_SSA3': 1.6349734460314116, 'H0_SSA4': 1.757498276233673, 'H0_SSA5': 1.6408348987499872, 'H0_SSA6': 1.6429049352804819, 'H0_SSA7': 1.5410810137788455, 'H0_MPA8': 0.0, 'H0_MPA9': 0.0, 'H1_SSA0': 1.5204497873783112, 'H1_SSA1': 1.726296795407931, 'H1_SSA2': 1.7595895811915399, 'H1_SSA3': 1.7196897546450296, 'H1_SSA4': 1.829413508872191, 'H1_SSA5': 1.8390584458907446, 'H1_SSA6': 2.1055170193314554, 'H1_SSA7': 2.269398490091165, 'H1_MPA8': 0.0, 'H1_MPA9': 0.0}}, 'runConfiguration': {'commonSettings': 'fake', 'Nevents': '-1', 'boards': {'0': {'ip': 'fake', 'opticalGroups': {'0': {'lpGBT': 'fake', 'hybrids': {'0': {'strips': [0, 1, 2, 3, 4, 5, 6, 7], 'pixels': [8, 9]}, '1': {'strips': [0, 1, 2, 3, 4, 5, 6, 7], 'pixels': [8, 9]}}}}}}}, 'runFile': 'https://cernbox.cern.ch/files/link/public/zcvWnJKEk7YgSBh//T2024_07_09_17_58_26_952865/output_bttaj.zip'}

test2 = {'runDate': '2025-01-21T16:33:25', 'runSession': 'session0', 'runStatus': 'done', 'runType': 'Type1', 'runBoards': {0: 'fake'}, 'runModules': {'fake_optical2': ('PS_26_10-IPG_00103', 749637543)}, 'runNoise': {749637543: {'H0_SSA0': 4.099950975179672, 'H0_SSA1': 3.762727153301239, 'H0_SSA2': 3.9623685499032337, 'H0_SSA3': 3.6007729331652323, 'H0_SSA4': 3.678371566534042, 'H0_SSA5': 3.5452729841073354, 'H0_SSA6': 3.711491898695628, 'H0_SSA7': 3.5207895656426746, 'H0_MPA8': 1.5034007266396656, 'H0_MPA9': 1.5381765266725174, 'H0_MPA10': 1.561102989575981, 'H0_MPA11': 1.6564606525935233, 'H0_MPA12': 1.5415886939774888, 'H0_MPA13': 1.5376611722672047, 'H0_MPA14': 1.4908423149958252, 'H0_MPA15': 1.4666612166756143, 'H1_SSA0': 3.6817489564418793, 'H1_SSA1': 3.8564588765303296, 'H1_SSA2': 3.8327214658260345, 'H1_SSA3': 4.042537007729212, 'H1_SSA4': 4.218453005949656, 'H1_SSA5': 4.451101825634638, 'H1_SSA6': 4.57403857310613, 'H1_SSA7': 4.96379288037618, 'H1_MPA8': 1.3482467160676606, 'H1_MPA9': 1.5684510056472694, 'H1_MPA10': 1.5006299837492407, 'H1_MPA11': 1.547164262497487, 'H1_MPA12': 1.5145373625525584, 'H1_MPA13': 1.5702755035754914, 'H1_MPA14': 1.6804338100211074, 'H1_MPA15': 1.4098257917173518}}, 'runConfiguration': {'commonSettings': 'fake', 'Nevents': '-1', 'boards': {'0': {'ip': 'fake', 'opticalGroups': {'2': {'lpGBT': 'fake', 'hybrids': {'0': {'strips': [0, 1, 2, 3, 4, 5, 6, 7], 'pixels': [8, 9, 10, 11, 12, 13, 14, 15]}, '1': {'strips': [0, 1, 2, 3, 4, 5, 6, 7], 'pixels': [8, 9, 10, 11, 12, 13, 14, 15]}}}}}}}, 'runFile': 'https://cernbox.cern.ch/files/link/public/zcvWnJKEk7YgSBh//T2025_01_22_10_11_18_522611/output_rilmv.zip'}


test3 = {
    'runDate': '2025-01-21T16:33:25',
    'runSession': 'session0',
    'runStatus': 'done',
    'runType': 'Type1',
    'runBoards': {0: 'fake'},
    'runModules': {
        'fake_optical2': ('PS_26_10-IPG_00103', 749637543)
    },
    'runNoise': {
        749637543: {
            'H0_SSA0': 4.099950975179672,
            'H0_SSA1': 3.762727153301239,
            'H0_SSA2': 3.9623685499032337,
            'H0_SSA3': 3.6007729331652323,
            'H0_SSA4': 3.678371566534042,
            'H0_SSA5': 3.5452729841073354,
            'H0_SSA6': 3.711491898695628,
            'H0_SSA7': 3.5207895656426746,
            'H0_MPA8': 1.5034007266396656,
            'H0_MPA9': 1.5381765266725174,
            # Removed H0_MPA10 through H0_MPA15
            'H1_SSA0': 3.6817489564418793,
            'H1_SSA1': 3.8564588765303296,
            'H1_SSA2': 3.8327214658260345,
            'H1_SSA3': 4.042537007729212,
            'H1_SSA4': 4.218453005949656,
            'H1_SSA5': 4.451101825634638,
            'H1_SSA6': 4.57403857310613,
            'H1_SSA7': 4.96379288037618,
            'H1_MPA8': 1.3482467160676606,
            'H1_MPA9': 1.5684510056472694
            # Removed H1_MPA10 through H1_MPA15
        }
    },
    'runConfiguration': {
        'commonSettings': 'fake',
        'Nevents': '-1',
        'boards': {
            '0': {
                'ip': 'fake',
                'opticalGroups': {
                    '2': {
                        'lpGBT': 'fake',
                        'hybrids': {
                            '0': {
                                # strips the same
                                'strips': [0, 1, 2, 3, 4, 5, 6, 7],
                                # keep only pixels 8,9
                                'pixels': [8, 9]
                            },
                            '1': {
                                'strips': [0, 1, 2, 3, 4, 5, 6, 7],
                                'pixels': [8, 9]
                            }
                        }
                    }
                }
            }
        }
    },
    'runFile': 'https://cernbox.cern.ch/files/link/public/zcvWnJKEk7YgSBh//T2025_01_22_10_11_18_522611/output_rilmv.zip'
}

test = {
    'runDate': '2024-06-19T10:56:26',
    'runSession': 'session80',
    'runStatus': 'done',
    'runType': 'Type1',
    'runBoards': {0: 'fake'},
    'runModules': {
        'fake_optical0': ('PS_26_05-IBA_00102', 3962125297)
    },
    'runNoise': {
        3962125297: {
            'H0_SSA0': 1.6686748445034028,
            'H0_SSA1': 1.642870126167933,
            'H0_SSA2': 1.8782315522432327,
            'H0_SSA3': 1.6349734460314116,
            'H0_SSA4': 1.757498276233673,
            'H0_SSA5': 1.6408348987499872,
            'H0_SSA6': 1.6429049352804819,
            'H0_SSA7': 1.5410810137788455,
            'H0_MPA8': 0.0,
            'H0_MPA9': 0.0,
            'H1_SSA0': 1.5204497873783112,
            'H1_SSA1': 1.726296795407931,
            'H1_SSA2': 1.7595895811915399,
            'H1_SSA3': 1.7196897546450296,
            'H1_SSA4': 1.829413508872191,
            'H1_SSA5': 1.8390584458907446,
            'H1_SSA6': 2.1055170193314554,
            'H1_SSA7': 2.269398490091165,
            'H1_MPA8': 0.0,
            'H1_MPA9': 0.0
        }
    },
    'runConfiguration': {
        'commonSettings': 'fake',
        'Nevents': '-1',
        'boards': {
            '0': {
                'ip': 'fake',
                'opticalGroups': {
                    '0': {
                        'lpGBT': 'fake',
                        'hybrids': {
                            '0': {
                                'strips': [0, 1, 2, 3, 4, 5, 6, 7],
                                'pixels': [8, 9]
                            },
                            '1': {
                                'strips': [0, 1, 2, 3, 4, 5, 6, 7],
                                'pixels': [8, 9]
                            }
                        }
                    }
                }
            }
        }
    },
    'runFile': 'https://cernbox.cern.ch/files/link/public/zcvWnJKEk7YgSBh//T2024_07_09_17_58_26_952865/output_bttaj.zip'
}

test5 = {'runNumber': 'run500006', 'runDate': '2025-03-24T17:35:03', 'runSession': 'session1', 'runStatus': 'done', 'runType': 'PSquickTest', 'runBoards': {0: 'fc7ot3'}, 'runModules': {'fc7ot3_optical4': ('PS_26_IBA-10007', 2351590349)}, 'runNoise': {2351590349: {'H0_SSA0': -1, 'H0_SSA1': -1, 'H0_SSA2': -1, 'H0_SSA3': -1, 'H0_SSA4': -1, 'H0_SSA5': -1, 'H0_SSA6': -1, 'H0_SSA7': -1, 'H0_MPA8': -1, 'H0_MPA9': -1, 'H0_MPA10': -1, 'H0_MPA11': -1, 'H0_MPA12': -1, 'H0_MPA13': -1, 'H0_MPA14': -1, 'H0_MPA15': -1, 'H1_SSA0': -1, 'H1_SSA1': -1, 'H1_SSA2': -1, 'H1_SSA3': -1, 'H1_SSA4': -1, 'H1_SSA5': -1, 'H1_SSA6': -1, 'H1_SSA7': -1, 'H1_MPA8': -1, 'H1_MPA9': -1, 'H1_MPA10': -1, 'H1_MPA11': -1, 'H1_MPA12': -1, 'H1_MPA13': -1, 'H1_MPA14': -1, 'H1_MPA15': -1}}, 'runConfiguration': {'commonSettings': 'fake', 'Nevents': '-1', 'boards': {'0': {'ip': 'fc7ot3:50001', 'opticalGroups': {'4': {'lpGBT': 'fake', 'hybrids': {'0': {'strips': [0, 1, 2, 3, 4, 5, 6, 7], 'pixels': [8, 9, 10, 11, 12, 13, 14, 15]}, '1': {'strips': [0, 1, 2, 3, 4, 5, 6, 7], 'pixels': [8, 9, 10, 11, 12, 13, 14, 15]}}}}}}}, 'runFile': 'https://cernbox.cern.ch/files/link/public/zcvWnJKEk7YgSBh//Run_500006/output_lqjoo.zip'}

#test_run_data = {

#{




# 'runOperator': 'Kristin Jackson',


# 'runStatus': 'done',
# 'runType': 'Type1',

#}


# URL of the API endpoint for updating a module
api_url = "http://%s:%d/addRun"%(ip, port)

print("import requests")
# Send a PUT request
json = test5
response = requests.post(api_url, json=json)
print("response = requests.post('%s', json=%s)" %(api_url, json))
print("response.status_code:", response.status_code)
print("response.text:", response.text)

print("response:", response)


# Check the response
if response.status_code == 201:
    print("Test created successfully")
else:
    print("Failed to update the module. Status code:", response.status_code)
    print(response.text)
    print(response.json())


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

