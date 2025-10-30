from moduleTest import verbose, ip, port, lpGBTids
#verbose = 100

from pprint import pprint
import requests

def evalMod(string):
    string = string.replace("true","True").replace("false","False").replace("null","None")
    return eval(string)

def handle_api_error(function_name, error_description, response, debug_curl_command=None, additional_info=None):
    """
    Generic error handler for API requests
    
    Args:
        function_name: Name of the function that failed
        error_description: Description of what failed
        response: The HTTP response object
        debug_curl_command: Optional curl command for debugging
        additional_info: Optional additional debug information
    """
    print()
    print(f"ERROR [{function_name}]: {error_description}. Status code:", response.status_code)
    print()
    if debug_curl_command:
        print("You can check this using:")
        print(debug_curl_command)
    print("Response:", response.status_code)
    print("Response:", response.content.decode())
    if additional_info:
        print()
        print("Debug info:")
        for info in additional_info:
            print(info)
    print()

def make_get_request(function_name, api_url, entity_type, entity_id=None):
    """
    Make a GET request with standardized error handling
    
    Args:
        function_name: Name of the calling function
        api_url: The API URL to call
        entity_type: Type of entity (e.g., "module", "test", "session")
        entity_id: Optional ID of the specific entity
    
    Returns:
        Parsed response data or None if error
    """
    response = requests.get(api_url)
    if response.status_code == 200:
        if verbose > 1:
            print(f"{entity_type.capitalize()} read successfully")
        return evalMod(response.content.decode().replace("null", "[]"))
    else:
        error_desc = f"Failed to get {entity_type}"
        if entity_id:
            error_desc += f" {entity_id}"
        
        curl_cmd = f"curl -X GET -H 'Content-Type: application/json' '{api_url}'"
        handle_api_error(function_name, error_desc, response, curl_cmd)
        return None

def make_post_request(function_name, api_url, json_data, entity_type, success_code=201):
    """
    Make a POST request with standardized error handling
    
    Args:
        function_name: Name of the calling function
        api_url: The API URL to call
        json_data: JSON data to send
        entity_type: Type of entity being created
        success_code: Expected success status code (default 201)
    
    Returns:
        Response object
    """
    response = requests.post(api_url, json=json_data)
    if response.status_code == success_code:
        if verbose > 1:
            print(f"{entity_type.capitalize()} created successfully")
    else:
        error_desc = f"Failed to create {entity_type}"
        curl_cmd = f"curl -X POST -H 'Content-Type: application/json' '{api_url}'"
        handle_api_error(function_name, error_desc, response, curl_cmd)
    return response

### upload the test result to the "tests" DB

## (obsolete) ##

def uploadTestToDB(testID, testResult = {}):
    if verbose>0: print("Calling uploadTestToDB()", testID)
    if verbose>2: pprint(testResult)
   
    # URL of the API endpoint for updating a module
    api_url = "http://%s:%d/tests"%(ip, port)
    
    # Send a PUT request
    response = requests.post(api_url, json=testResult)
    
    # Check the response
    if response.status_code == 201:
        if verbose>1: print("Test %s created successfully"%testID)
    else:
        print()
        print(f"ERROR [uploadTestToDB]: Failed to create test {testID}. Status code:", response.status_code)
        print()
        print("You can check if the test exists in the database using:")
        print(f"curl -X GET -H 'Content-Type: application/json' 'http://{ip}:{port}/tests/{testID}'")
        print("Response:", response.status_code)
        print("Response:", response.content.decode())
        print()

### upload the new Run to the "module_test" and "test_run" DB 

def uploadRunToDB(newRun = {}):
    if verbose>0: print("Calling uploadRunToDB()")
    if len(newRun["runDate"].split("-")[0])==2:
        print("WARNING: runDate is in the wrong format. It should be YYYY-MM-DD HH:MM:SS. Fixing it.")
        print ("Before:", newRun["runDate"])
        newRun["runDate"] = "20" + newRun["runDate"]
        print ("After:", newRun["runDate"])
    if verbose>2: pprint(newRun)
   
    # URL of the API endpoint for updating a module
    api_url = "http://%s:%d/addRun"%(ip, port)
    
    # Send a PUT request
    response = requests.post(api_url, json=newRun)
    if verbose>0: print(response)
    
    # Check the response
    if response.status_code == 201:
        if verbose>1: print("Run uploaded successfully")
    else:
        print()
        print(f"ERROR [uploadRunToDB]: Failed to upload run. Status code:", response.status_code)
        print()
        print("You can check if the run endpoint exists using:")
        print(f"curl -X POST -H 'Content-Type: application/json' 'http://{ip}:{port}/addRun'")
        print("Response:", response.status_code)
        print("Response:", response.content.decode())
        print()
        print("Debug info:")
        print("response = requests.post(api_url, json=newRun)")
        print(api_url)
        print(newRun)
    
    if verbose>1:
        print(response.json()['message'])
    
    print(response.json())
    
    return response.json()['test_runName']

### read the test result from DB

def getTestFromDB(testID):
    if verbose>0: print("Calling getTestFromDB()", testID)
    api_url = "http://%s:%d/tests/%s"%(ip, port, testID)
    result = make_get_request("getTestFromDB", api_url, "test", testID)
    return result if result is not None else evalMod("{}")

### read the list of sessions

def getListOfSessionsFromDB():
    if verbose>0: print("Calling getListOfSessionsFromDB()")
    api_url = "http://%s:%d/sessions"%(ip, port)
    result = make_get_request("getListOfSessionsFromDB", api_url, "sessions list")
    return result if result is not None else []

### read the list of modules

def getListOfModulesFromDB():
    if verbose>0: print("Calling getListOfModulesFromDB()")
    api_url = "http://%s:%d/modules"%(ip, port)
    result = make_get_request("getListOfModulesFromDB", api_url, "modules list")
    return result if result is not None else []

### read the test modules analysis

def getListOfAnalysisFromDB():
    if verbose>0: print("Calling getListOfAnalysisFromDB()")
    api_url = "http://%s:%d/module_test_analysis"%(ip, port)
    result = make_get_request("getListOfAnalysisFromDB", api_url, "analysis list")
    return result if result is not None else []

### read the module test result from DB

def getSessionFromDB(testID):
    if verbose>0: print("Calling getSessionFromDB()", testID)
    api_url = "http://%s:%d/sessions/%s"%(ip, port, testID)
    result = make_get_request("getSessionFromDB", api_url, "session", testID)
    return result if result is not None else evalMod("{}")

### read the module test result from DB

def getModuleTestFromDB(testID):
    if verbose>0: print("Calling getModuleTestFromDB()", testID)
    api_url = "http://%s:%d/module_test/%s"%(ip, port, testID)
    result = make_get_request("getModuleTestFromDB", api_url, "module test", testID)
    return result if result is not None else evalMod("{}")

### get run from DB

def getRunFromDB(testID):
    if verbose>0: print("Calling getRunFromDB()", testID)
    api_url = "http://%s:%d/test_run/%s"%(ip, port, testID)
    result = make_get_request("getRunFromDB", api_url, "run", testID)
    return result if result is not None else evalMod("{}")

### read a module from DB, given the moduleName

def getModuleFromDB(moduleName=1234):
    if verbose>0: print("Calling getModuleFromDB()", moduleName)
    api_url = "http://%s:%d/modules/%s"%(ip, port, moduleName)
    result = make_get_request("getModuleFromDB", api_url, "module", moduleName)
    return result if result is not None else evalMod("{}")

### read the fiber connections of slot X

def getFiberLink(slot):
    if verbose>0: print("Calling getFiberLink()", slot)
    out = getConnectionMap(slot)
    if out is None:
        return None, None
    
    fc7 = None
    optical = None
    for link in out:
        if "connections" in out[link]:
           if len(out[link]["connections"])>0:
             last = out[link]["connections"][-1]
             if "FC7" in last["cable"]:
                 ## expect 2 "fiber" pointing to the same FC7 and optical group
                 if fc7: assert(fc7==last["cable"]) 
                 if optical: assert(optical==last["det_port"][0])
                 fc7 = last["cable"]
                 optical = last["det_port"][0]
        else:
            if "error" in out[link]: print(out[link]["error"])
            #it might be a new module to be added into the database
            #raise Exception("Error in Calling getModuleConnectedToFC7()",fc7, og)
    return fc7, optical

### read the fiber connections of slot X

def getConnectionMap(moduleName):
    if verbose>0: print("Calling getConnectionMap()", moduleName)
    api_url = "http://%s:%d/snapshot"%(ip, port)
    
    snapshot_data = {
        "cable": moduleName,
        "side": "crateSide"
    }
    response = requests.post(api_url, json=snapshot_data)
    
    if response.status_code == 200:
        if verbose>1: print("Module read successfully")
        out = evalMod(response.content.decode())
        return out
    else:
        print()
        print(f"ERROR [getConnectionMap]: Failed to get connection map for {moduleName}. Status code:", response.status_code)
        print()
        print("Check if module %s exists in the database: http://pccmslab1.pi.infn.it:5000/static/connections.html "%moduleName)
        print("You can check if the module exists in the database using:")
        print(f"curl -X POST -H 'Content-Type: application/json' -d '{{\"cable\":\"{moduleName}\", \"side\":\"crateSide\"}}' 'http://{ip}:{port}/snapshot'")
        print("Response:", response.status_code)
        print("Response:", response.content.decode())
        print()
        return None

from pprint import pformat
def saveMapToFile(json, filename):
    with open(filename, 'w') as f:
        f.write(pformat(json))
    print("Saved to", filename) 


### read the expected module connected of slot board X optical group Y

def getModuleConnectedToFC7(fc7, og):
    if verbose>0: print("Calling getModuleConnectedToFC7()",fc7, og)
    api_url = "http://%s:%d/snapshot"%(ip, port)
    
    snapshot_data = {
        "cable": fc7,
        "side": "detSide"
    }
    response = requests.post(api_url, json=snapshot_data)
    
    if response.status_code == 200:
        if verbose>1: print("Module read successfully")
    else:
        print()
        print(f"ERROR [getModuleConnectedToFC7]: Failed to get module connected to {fc7} {og}. Status code:", response.status_code)
        print()
        print("You can check if the FC7 exists in the database using:")
        print(f"curl -X POST -H 'Content-Type: application/json' -d '{{\"cable\":\"{fc7}\", \"side\":\"detSide\"}}' 'http://{ip}:{port}/snapshot'")
        print("Response:", response.status_code)
        print("Response:", response.content.decode())
        print()
    out = evalMod(response.content.decode())
    
    moduleName = None
    for link in out:
    
        if "connections" in out[link] and len(out[link]["connections"])>0:
            if out[link]["det_port"]==og and len(out[link]["connections"])>0:
                last = out[link]["connections"][-1]
                if len(last["det_port"])>0: continue ## if it has something on det side, it is a cable, not a module.
                ## expect 2 "fiber" pointing to the same FC7 and optical group
                if moduleName: assert(moduleName==last["cable"]) 
                moduleName = last["cable"]
        else:
            if "error" in out[link]: print(out[link]["error"])
            #it might be a new module to be added into the database
            #raise Exception("Error in Calling getModuleConnectedToFC7()",fc7, og)
    if moduleName == None:
        print()
        print("ERROR [getModuleConnectedToFC7]: Could not find module connected to FC7 %s and optical group %s"%(fc7, og))
        print()
    return moduleName

### check from DB if the module is 5G or 10G, looking at module["children"]["PS Read-out Hybrid"]["details"]["ALPGBT_BANDWIDTH"]
def getModuleBandwidthFromDB(moduleName):
    if verbose>0: print("Calling getModuleBandwidthFromDB()", moduleName)
    module = getModuleFromDB(moduleName)
    if "children" in module and "PS Read-out Hybrid" in module["children"] and "details" in module["children"]["PS Read-out Hybrid"] and "ALPGBT_BANDWIDTH" in module["children"]["PS Read-out Hybrid"]["details"]:
        return module["children"]["PS Read-out Hybrid"]["details"]["ALPGBT_BANDWIDTH"]
    elif not "children" in module:
        print ("Error: Could not find children in module %s"%moduleName)
    elif not "PS Read-out Hybrid" in module["children"]:
        print ("Error: Could not find PS Read-out Hybrid in module %s"%moduleName)
    elif not "details" in module["children"]["PS Read-out Hybrid"]: 
        print ("Error: Could not find details in module %s"%moduleName)
    import pprint
    print(module)
    return "Not Found"
    

### read the list of sessions

def getListOfSessionsFromDB():
    if verbose>0: print("Calling getListOfSessionsFromDB()")
    api_url = "http://%s:%d/sessions"%(ip, port)
    response = requests.get(api_url)
    if response.status_code == 200:
        if verbose>1: print("Session read successfully")
    else:
        print()
        print(f"ERROR [getListOfSessionsFromDB]: Failed to get list of sessions. Status code:", response.status_code)
        print()
        print("You can check if the sessions endpoint exists using:")
        print(f"curl -X GET -H 'Content-Type: application/json' 'http://{ip}:{port}/sessions'")
        print("Response:", response.status_code)
        print("Response:", response.content.decode())
        print()
    return evalMod(response.content.decode())

### read the list of modules

def getListOfModulesFromDB():
    if verbose>0: print("Calling getListOfModulesFromDB()")
    api_url = "http://%s:%d/modules"%(ip, port)
    response = requests.get(api_url)
    if response.status_code == 200:
        if verbose>1: print("Session read successfully")
    else:
        print()
        print(f"ERROR [getListOfModulesFromDB]: Failed to get list of modules. Status code:", response.status_code)
        print()
        print("You can check if the modules endpoint exists using:")
        print(f"curl -X GET -H 'Content-Type: application/json' 'http://{ip}:{port}/modules'")
        print("Response:", response.status_code)
        print("Response:", response.content.decode())
        print()
    return evalMod(response.content.decode())


### read the test modules analysis

def getListOfAnalysisFromDB():
    if verbose>0: print("Calling getListOfAnalysisFromDB()")
    api_url = "http://%s:%d/module_test_analysis"%(ip, port)
    response = requests.get(api_url)
    if response.status_code == 200:
        if verbose>1: print("Session read successfully")
    else:
        print()
        print(f"ERROR [getListOfAnalysisFromDB]: Failed to get list of analysis. Status code:", response.status_code)
        print()
        print("You can check if the analysis endpoint exists using:")
        print(f"curl -X GET -H 'Content-Type: application/json' 'http://{ip}:{port}/module_test_analysis'")
        print("Response:", response.status_code)
        print("Response:", response.content.decode())
        print()
    return evalMod(response.content.decode())

### read the module test result from DB

def getSessionFromDB(testID):
    if verbose>0: print("Calling getSessionFromDB()", testID)
    api_url = "http://%s:%d/sessions/%s"%(ip, port, testID)
    response = requests.get(api_url)
    if response.status_code == 200:
        if verbose>1: print("Session read successfully")
    else:
        print()
        print(f"ERROR [getSessionFromDB]: Failed to get session {testID}. Status code:", response.status_code)
        print()
        print("You can check if the session exists in the database using:")
        print(f"curl -X GET -H 'Content-Type: application/json' 'http://{ip}:{port}/sessions/{testID}'")
        print("Response:", response.status_code)
        print("Response:", response.content.decode())
        print()
    return evalMod(response.content.decode())

### read the module test result from DB

def getModuleTestFromDB(testID):
    if verbose>0: print("Calling getModuleTestFromDB()", testID)
    api_url = "http://%s:%d/module_test/%s"%(ip, port, testID)
    response = requests.get(api_url)
    if response.status_code == 200:
        if verbose>1: print("Module test read successfully")
    else:
        print()
        print(f"ERROR [getModuleTestFromDB]: Failed to get module test {testID}. Status code:", response.status_code)
        print()
        print("You can check if the module test exists in the database using:")
        print(f"curl -X GET -H 'Content-Type: application/json' 'http://{ip}:{port}/module_test/{testID}'")
        print("Response:", response.status_code)
        print("Response:", response.content.decode())
        print()
    return evalMod(response.content.decode())

### get run from DB

def getRunFromDB(testID):
    if verbose>0: print("Calling getRunFromDB()", testID)
    api_url = "http://%s:%d/test_run/%s"%(ip, port, testID)
    response = requests.get(api_url)
    if response.status_code == 200:
        if verbose>1: print("Module read successfully")
    else:
        print()
        print(f"ERROR [getRunFromDB]: Failed to get run {testID}. Status code:", response.status_code)
        print()
        print("You can check if the run exists in the database using:")
        print(f"curl -X GET -H 'Content-Type: application/json' 'http://{ip}:{port}/test_run/{testID}'")
        print("Response:", response.status_code)
        print("Response:", response.content.decode())
        print()
    return evalMod(response.content.decode())

### read a module from DB, given the moduleName

def getIVscansOfModule(moduleName=1234):
    if verbose>0: print("Calling getIVscansOfModule()", moduleName)
    api_url = "http://%s:%d/iv_scans/%s"%(ip, port, moduleName)
    response = requests.get(api_url)
    if response.status_code == 200:
        if verbose>1: print("IV scan read successfully")
    else:
        print()
        print(f"ERROR [getIVscansOfModule]: Failed to read IV scans for module {moduleName}. Status code:", response.status_code)
        print("You can check if the module exists in the database using:")
        print(f"curl -X GET -H 'Content-Type: application/json' 'http://{ip}:{port}/modules/{moduleName}'")
        print("Response:", response.status_code)
        print("Response:", response.content.decode())
        print()
    return evalMod(response.content.decode().replace("null","[]"))

### update the "tests" parameter of module in DB using updatedTestList 

def addTestToModuleDB(updatedTestList, moduleName):
    if not updatedTestList or len(updatedTestList)<1: raise Exception("updatedTestList is empty. " + str(updatedTestList))
    if verbose>0: print("Calling addTestToModuleDB()", updatedTestList, moduleName)
    api_url = "http://%s:%d/modules/%s"%(ip, port, moduleName)
    updated_module = { "tests": updatedTestList }
    response = requests.put(api_url, json=updated_module)
    if response.status_code == 200:
        if verbose>1: print("Module updated successfully")
    else:
        print()
        print(f"ERROR [addTestToModuleDB]: Failed to update module {moduleName}. Status code:", response.status_code)
        print()
        print("You can check if the module exists in the database using:")
        print(f"curl -X GET -H 'Content-Type: application/json' 'http://{ip}:{port}/modules/{moduleName}'")
        print("Response:", response.status_code)
        print("Response:", response.content.decode())
        print()

def createAnalysis(json):
    if verbose>0: print("Calling createAnalysis()")
    api_url = "http://%s:%d/module_test_analysis"%(ip, port)
#    json = {'moduleTestAnalysisName': analysisName}
    response = requests.post(api_url, json=json)
    print(response)
    print(response.content.decode())
    print(response.status_code)
    if response.status_code == 201:
        if verbose>1: print("Single module test analysis added successfully")
    else:
        print()
        print(f"ERROR [createAnalysis]: Failed to create analysis. Status code:", response.status_code)
        print()
        print("You can check if the analysis endpoint exists using:")
        print(f"curl -X POST -H 'Content-Type: application/json' 'http://{ip}:{port}/module_test_analysis'")
        print("Response:", response.status_code)
        print("Response:", response.content.decode())
        print()
    return response.status_code

def appendAnalysisToModule(analysisName):
    if verbose>0: print("Calling appendAnalysisToModule()", analysisName)
    api_url = "http://%s:%d/addAnalysis"%(ip, port)
    json = {'moduleTestAnalysisName': analysisName}
    response = requests.get(api_url, params=json)
    if verbose>4: 
        print("Calling request.get(%s, %s)"%(api_url, json))
        print(response)
        print(response.content.decode())
        print(response.status_code)
    if response.status_code == 200:
        if verbose>1: print("Analysis appended to existing module successfully")
    else:
        print()
        print(f"ERROR [appendAnalysisToModule]: Failed to append analysis {analysisName}. Status code:", response.status_code)
        print()
        print("You can check if the analysis endpoint exists using:")
        print(f"curl -X GET 'http://{ip}:{port}/addAnalysis?moduleTestAnalysisName={analysisName}'")
        print("Response:", response.status_code)
        print("Response:", response.content.decode())
        print()
    return response.status_code

# ## check if the expected modules match the modules declared in the database for the slots
# def checkIfExpectedModulesMatchModulesInDB(board, slots, modules, args):
#     from databaseTools import getModuleConnectedToFC7, getModuleBandwidthFromDB
#     for i, slot in enumerate(slots):
#         error = None
#         moduleFromDB = getModuleConnectedToFC7(board.upper(), "OG%s"%slot)
#         if modules[i] == "auto":  
#             modules[i] = moduleFromDB
#             print("You selected 'auto' for the module in board %s and slot %s. I will use the module %s declared in the connection database."%(board, slot, moduleFromDB))
#         moduleFromCLI = modules[i]
#         print("board %s, slot %s, moduleFromDB %s, moduleFromCLI %s"%(board, slot, moduleFromDB, moduleFromCLI))
#         moduleBandwidth = getModuleBandwidthFromDB(moduleFromCLI)
#         print("Expected module %s. According to Pisa db is %s"%(moduleFromCLI, moduleBandwidth))
#         if moduleBandwidth == "5Gbps" and args.g10:
#             raise Exception("Module %s is declared in the database as 5Gbps, but you are trying to run the test with 10Gbps firmware."%moduleFromDB)
#         elif moduleBandwidth == "10Gbps" and args.g5:
#             raise Exception("Module %s is declared in the database as 10Gbps, but you are trying to run the test with 5Gbps firmware."%moduleFromDB)
#         if moduleFromDB == None:
#             from databaseTools import getFiberLink
#             fc7, og = getFiberLink(moduleFromCLI)
#             if fc7 == None:
#                 print("No module declared in the database for board %s and slot %s."%(board.upper(), "OG%s"%slot))
#                 if args.addNewModule:
#                     print("It is ok, as you are going to add new modules to the database.")
#                 else: 
#                     error = "No module declared in the database for board %s and slot %s. If you are not adding a new module, something is wrong. If you want to add a new module, please use --addNewModule option."%(board.upper(), "OG%s"%slot)
#                     print(error)
#             else:
#                 error = "Module %s is already in the connection database and it is expected in board %s and slot %s, not in board %s and slot %s. You can avoid this error using --ignoreConnection option."%(moduleFromCLI, fc7, og, board.upper(), "OG%s"%slot)
#                 print(error)
#         else:
#             if moduleFromDB != moduleFromCLI:
#                 error = "Module %s declared in the database for board %s and slot %s does not match the module declared in the command line (%s)."%(moduleFromDB, board, slot, modules[i])
#                 print(error)
#             else:
#                 print("Module %s declared in the database for board %s and slot %s matches the module declared in the command line (%s)."%(moduleFromDB, board, slot, modules[i]))
#         if error: 
#             if args.ignoreConnection:
#                 print("WARNING: --ignoreConnection option is active. I will not throw exception if there is a mismatch between the database connection and the module declared.")
#                 print("WARNING: %s"%error)
#             else:
#                 raise Exception(error+" You can skip this error using --ignoreConnection flag.")
#     return

def createSession(message, moduleList):
    from datetime import datetime
    if verbose>0: print("Calling createSession()")
    splitted = message.split("|")
    if len(splitted)<2:
        raise Exception("Error: Message should have at least two fields (author|message)separated by |. You used -m %s"%message)
    operator = splitted[0]
    message = "|".join(splitted[1:])
    print (operator, message)
    sessionJson={
        "operator": operator,
        "description": message,
        "timestamp": datetime.now().strftime('%Y-%m-%dT%H:%M:%S'),
        "modulesList": moduleList,
    }
    #create new session in DB
    api_url = "http://%s:%d/sessions"%(ip, port)
    response = requests.post(api_url, json=sessionJson)
    print(response)
    print(response.content.decode())
    print(response.status_code)
    if response.status_code == 201:
        if verbose>1: print("Session added successfully")
    else:
        print()
        print(f"ERROR [createSession]: Failed to create session. Status code:", response.status_code)
        print()
        print("You can check if the session endpoint exists using:")
        print(f"curl -X POST -H 'Content-Type: application/json' 'http://{ip}:{port}/sessions'")
        print("Response:", response.status_code)
        print("Response:", response.content.decode())
        print()
    try:
        sessionName = eval(response.content.decode())["sessionName"]
    except:
        raise Exception("Something wrong in adding the session. Please check the response: %s"%response.content.decode())
    return sessionName


    success, result = self.make_api_request("sessions", "POST", session)    
    self.current_session = result["sessionName"]

#    self.current_module_id = self.moduleLE.text()
#    self.current_session_operator = self.operatorLE.text()
#    self.current_session_comments = self.commentsLE.text()
    print(self.current_session)
    return self.current_session

    return "session1"

#new_test = {
#    "testID": "T001",
#    "modules_list": ["M1", "M2"],
#    "testType": "Type1",
#    "testDate": "2023-11-01",
#    "testStatus": "completed",
#    "testResults": {}
#}

#def addTestToModuleDBNew():
#    if verbose>0: print("Calling addTestToModuleDBNew()")
#    api_url = "http://%s:%d/addTest"%(ip, port)
#    response = requests.put(api_url, json=new_test)
#    if response.status_code == 201:
#        if verbose>1: print("Module added successfully")
#    else:
#        print("Failed to add the module. Status code:", response.status_code)

### read a module from DB, given the moduleName

def getModuleFromDB(moduleName=1234):
    if verbose>0: print("Calling getModuleFromDB()", moduleName)
    api_url = "http://%s:%d/modules/%s"%(ip, port, moduleName)
    response = requests.get(api_url)
    if response.status_code == 200:
        if verbose>1: print("Module read successfully")
    else:
        print()
        print(f"ERROR [getModuleFromDB]: Failed to get module {moduleName}. Status code:", response.status_code)
        print()
        print("You can check if the module exists in the database using:")
        print(f"curl -X GET -H 'Content-Type: application/json' 'http://{ip}:{port}/modules/{moduleName}'")
        print("Response:", response.status_code)
        print("Response:", response.content.decode())
        print()
    return evalMod(response.content.decode().replace("null","[]"))

### create the maps hwTomoduleName and hwToMongoID to convert the hardware lpGBT ID to module ID and mongo ID.
# -1 = missing module (module didn't work during the test)

def makeModuleNameMapFromDB():
    if verbose>0: print("Calling makeModuleNameMapFromDB()")
    api_url = "http://%s:%d/modules"%(ip, port)
    response = requests.get(api_url)
    modules = evalMod(response.content.decode().replace("null","[]"))
#    if len(modules)==0:
#        raise Exception("\n'modules' database is empty. Please check: \ncurl -X GET -H 'Content-Type: application/json' 'http://192.168.0.45:5000/modules'")
    hwToModuleName = {} ## hwId --> moduleName
    hwToMongoID = {} ## hwId --> mongoId
    for module in modules:
        hwId = -1
        if "hwId" in module:
            hwId = int(module["hwId"])
#        if "children" in module and "lpGBT" in module["children"] and "CHILD_SERIAL_NUMBER" in module["children"]["lpGBT"]:
        if "children" in module and "lpGBT" in module["children"]:
                hwId = int(module["children"]["lpGBT"]["CHILD_SERIAL_NUMBER"])
        hwToModuleName[hwId] = module["moduleName"]
        hwToMongoID[hwId] = module["_id"]
        if hwId<0:
            print('WARNING: Missing module["children"]["lpGBT"]["CHILD_SERIAL_NUMBER"] (ie. hardwareID) in module %s'%module["moduleName"])
    
    ### hard-code some modules, waiting to have these numbers in the database
    for i, lpGBTid in enumerate(lpGBTids):
        try:
            if not lpGBTid in hwToModuleName: hwToModuleName[lpGBTid] = modules[i]["moduleName"]
            if not lpGBTid in hwToMongoID: hwToMongoID[lpGBTid] = modules[i]["_id"]
        except:
            print("WARNING: 'modules' database is empty. Please check: \ncurl -X GET -H 'Content-Type: application/json' 'http://192.168.0.45:5000/modules'")
            if not lpGBTid in hwToModuleName: hwToModuleName[lpGBTid] = str(i)
            if not lpGBTid in hwToMongoID: hwToMongoID[lpGBTid] = str(i)
        
    ### "-1", ie. missing modules, should go in "-1"
    hwToModuleName["-1"] = "-1"
    hwToMongoID["-1"] = "-1"
    return hwToModuleName, hwToMongoID

### This code allow you to test this code using "python3 databaseTools.py"
def addNewModule(moduleName, id_):
    if verbose>0: print("addNewModule(%s, %s)"%(moduleName, id_))
   
    # URL of the API endpoint for updating a module
    api_url = "http://%s:%d/modules"%(ip, port)
    
    # Send a PUT request
    json = {
        "moduleName": moduleName,
        "position": "cleanroom",
        "logbook": {"entry": "Initial setup"},
        "local_logbook": {"entry": "Local setup"},
        "ref_to_global_logbook": [],
        "status": "operational",
        "overall_grade": "A",
        "hwId": id_,
        "tests": []
    }

    response = requests.post(api_url, json=json)
    if verbose>1: print(response)
    print(response.json())
    
    # Check the response
    if response.status_code == 201:
        if verbose>1: print("Module %s uploaded successfully (hwId=%d)"%(moduleName, id_))
    else:
        print()
        print(f"ERROR [addNewModule]: Failed to add new module {moduleName}. Status code:", response.status_code)
        print()
        print("You can check if the module endpoint exists using:")
        print(f"curl -X POST -H 'Content-Type: application/json' 'http://{ip}:{port}/modules'")
        print("Response:", response.status_code)
        print("Response:", response.content.decode())
        print()
        print("Debug info:")
        print("response = requests.post(api_url, json=newRun)")
        print(api_url)
    
    if verbose>1:
        print(response.json()['message'])
    return response.json()

###  This code allow you to add missing field in an already existing module
def updateNewModule(moduleName, id_):
    if verbose>0: print("updateNewModule(%s, %s)"%(moduleName, id_))
    # URL of the API endpoint for updating a module
    api_url = "http://%s:%d/modules/%s"%(ip, port, moduleName)
    response = requests.get(api_url)
    moduleJson = evalMod(response.content.decode().replace("null","[]"))
    if moduleJson:
        print("Module %s already exists"%moduleName)
        if not hasattr(moduleJson,"moduleName") or not moduleJson["moduleName"]: moduleJson["moduleName"] = moduleName
        if not hasattr(moduleJson,"hwId") or moduleJson["hwId"]: moduleJson["hwId"] = id_
        if not hasattr(moduleJson,"position") or moduleJson["position"]: moduleJson["position"] = "cleanroom"
        if not hasattr(moduleJson,"logbook") or moduleJson["logbook"]: moduleJson["logbook"] = {"entry": "Initial setup"}
        if not hasattr(moduleJson,"local_logbook") or moduleJson["local_logbook"]: moduleJson["local_logbook"] = {"entry": "Local setup"}
        if not hasattr(moduleJson,"ref_to_global_logbook") or moduleJson["ref_to_global_logbook"]: moduleJson["ref_to_global_logbook"] = []
        if not hasattr(moduleJson,"status") or moduleJson["status"]: moduleJson["status"] = "operational"
        if not hasattr(moduleJson,"overall_grade") or moduleJson["overall_grade"]: moduleJson["overall_grade"] = "A"
        if not hasattr(moduleJson,"tests") or moduleJson["tests"]: moduleJson["tests"] = []
        print("Updating module %s with:"%moduleName)
        del moduleJson["_id"]
        pprint(moduleJson)
        response = requests.put(api_url, json=moduleJson)
        print("Done ", response)
        ## print response text
        print(response.text)
        print(response.json())
        print(response.json())
        return response.json()
    else:
        for module in modules:
            print(module)
        print("Module %s does not exist. Adding it. Launch addNewModule(%s,%s)"%(moduleName, moduleName, id_))
        return addNewModule(moduleName, id_)
        
#    if len(modules)==0:
#        raise Exception("\n'modules' database is empty. Please check: \ncurl -X GET -H 'Content-Type: application/json' 'http://192.168.0.45:5000/modules'")
    

### Update firmaware version in a FC7OT board
# curl -X PUT -H "Content-Type: application/json" -d '{"firmware": "abcd", "firmware_timestamp" : "12349032123" }' 'cmslabserver:5000/cables/FC7OT7' 

def updateFirmwareVersionInFC7OT(board, firmware, firmware_timestamp):
    board = board.upper()
    if verbose>0: print("Calling updateFirmwareVersionInFC7OT(%s, %s, %s)"%(board, firmware, firmware_timestamp))
    # URL of the API endpoint for updating a module
    api_url = "http://%s:%d/cables/%s"%(ip, port, board)
    response = requests.get(api_url)
    cableJson = evalMod(response.content.decode().replace("null","[]"))
    if response.status_code == 200:
        if verbose>0: print("Board %s found in database"%board)
        #print("Cable json:", cableJson)
        newFirmwareInfo = {"firmware": firmware, "firmware_timestamp": firmware_timestamp}
        response = requests.put(api_url, json=newFirmwareInfo)
        if verbose>0: print("Updated firmware version of board %s to %s (%s)"%(board, firmware, firmware_timestamp))
        ## print response text
        return response
    else:
        print("ERROR: Could not find board %s in the database."%board)
        raise Exception("Board %s does not exist. Please check the board name. You can check the list of boards using:\ncurl -X GET -H 'Content-Type: application/json' 'http://%s:%d/cables'"%(board, ip, port))

### Get firmware version in a FC7OT board
def getFirmwareVersionInFC7OT(board):
    board = board.upper()
    if verbose>0: print("Calling getFirmwareVersionInFC7OT(%s)"%(board))
    # URL of the API endpoint for updating a module
    api_url = "http://%s:%d/cables/%s"%(ip, port, board)
    response = requests.get(api_url)
    cableJson = evalMod(response.content.decode().replace("null","[]"))
    if response.status_code == 200:
        if verbose>0: print("Board %s found in database"%board)
        #print("Cable json:", cableJson)
        if "firmware" in cableJson and "firmware_timestamp" in cableJson:
            return cableJson["firmware"], cableJson["firmware_timestamp"]
        else:
            print("ERROR: Could not find firmware information in board %s in the database."%board)
            print("It might be the first time you use this board, so I will return None, None.")
            #raise Exception("Board %s does not have firmware information. Please update it using:\ncurl -X PUT -H 'Content-Type: application/json' -d '{\"firmware\": \"abcd\", \"firmware_timestamp\" : \"12349032123\" }' 'http://%s:%d/cables/%s'"%(board, ip, port, board))
            return None, None
    else:
        print("ERROR: Could not find board %s in the database."%board)
        raise Exception("Board %s does not exist. Please check the board name. You can check the list of boards using:\ncurl -X GET -H 'Content-Type: application/json' 'http://%s:%d/cables'"%(board, ip, port))

### Get the optical group and board from a single slotBI

def getOpticaGroupAndBoardFromBISlot(slotBI):
    """
    Get the optical group and board from a single slotBI.
    slotBI is a number between 0 and 8 (slot in the burn-in).
    Returns: (fc7, og) where fc7 is the FC7 board name and og is the optical group number
    """
    if verbose>0: print("Calling getOpticaGroupAndBoardFromBISlot()", slotBI)
    crate = "B%s"%slotBI
    out = getConnectionMap(crate)
    
    if out is None:
        raise Exception("Error in calling getOpticaGroupAndBoardFromBISlot() for slot %s. Crate %s does not exist in the database (see http://pccmslab1.pi.infn.it:5000/static/connections.html)"%(slotBI, crate))
    
    fc7 = None
    og = None
    for el in out.values():
        if "connections" in el and len(el["connections"])>0:
            last = el["connections"][-1]
            if "cable" in last and last["cable"][:5]== "FC7OT":
                og = last["det_port"][0].split("OG")[-1]  # Return the optical group number, e.g., "10" from "OG10"
                fc7 = last["cable"]
                if verbose>600: print("Optical group %s and board %s found for slot %s"%(og, fc7, slotBI))
                break
    
    if fc7 is None or og is None:
        raise Exception("Error: Could not find any FC7OT connected to slot %s (crate %s). See http://pccmslab1.pi.infn.it:5000/static/connections.html "%(slotBI, crate))
    
    return fc7, og

### Get the optical group and board from the slotBI

def getOpticaGroupAndBoardFromSlots(slotsBI):
    """
    Get the optical group and board from the slotBI.
    slotBI is a number between 0 and 8 (slot in the burn-in).
    Returns: (fc7, optical_group) where fc7 is the FC7 board name and optical_group is a list of optical group numbers
    """
    optical_group = []
    fc7 = None
    for slotBI in slotsBI:
        fc7_single, og_single = getOpticaGroupAndBoardFromBISlot(slotBI)
        
        if not fc7:
            fc7 = fc7_single
        else:
            if fc7 != fc7_single:
                raise Exception("Error: Found different FC7 for burnin in slots %s. %s and %s. You cannot run simultaneously on two different FC7s."%(slotBI, fc7, fc7_single))
        
        optical_group.append(og_single)
    
    return fc7, optical_group

def getConnectionMapFromFC7(fc7):
    """
    Get the connection map for a given FC7 board (detSide view).
    Returns the connection map or None if error.
    """
    if verbose>0: print("Calling getConnectionMapFromFC7()", fc7)
    api_url = "http://%s:%d/snapshot"%(ip, port)
    
    snapshot_data = {
        "cable": fc7,
        "side": "detSide"
    }
    response = requests.post(api_url, json=snapshot_data)
    
    if response.status_code == 200:
        if verbose>1: print("FC7 connection map read successfully")
        out = evalMod(response.content.decode())
        return out
    else:
        print()
        print(f"ERROR [getConnectionMapFromFC7]: Failed to get connection map for FC7 {fc7}. Status code:", response.status_code)
        print()
        print("You can check if the FC7 exists in the database using:")
        print(f"curl -X POST -H 'Content-Type: application/json' -d '{{\"cable\":\"{fc7}\", \"side\":\"detSide\"}}' 'http://{ip}:{port}/snapshot'")
        print("Response:", response.status_code)
        print("Response:", response.content.decode())
        print()
        return None

def getSlotBIFromModuleConnectionMap(connectionMapModule):
    """
    Get the slotBI from the module connection map (detSide view).
    slotBI is a number between 0 and 8 (slot in the burn-in).
    Returns: slotBI as an integer, or None if not found
    """
    if verbose>0: print("Calling getSlotBIFromModuleConnectionMap()")
    if connectionMapModule is None:
        raise Exception("Error in calling getSlotBIFromModuleConnectionMap(). Module connection map does not exist in the database (see http://pccmslab1.pi.infn.it:5000/static/connections.html)")

    for el in connectionMapModule.values():
        if "connections" in el:
            for conn in el["connections"]:
                if "cable" in conn and conn["cable"].startswith("B") and conn["cable"][1].isdigit(): ## expect "B0" to "B8"
                    slotBI = int(conn["cable"].replace("B",""))
                    if verbose>1: print("Found slotBI %s for module in connection map"%(slotBI))
                    return slotBI
    print("ERROR [getSlotBIFromModuleConnectionMap]: Could not find any slotBI in the module connection map")
    return None

#module.get("children").get("PS Read-out Hybrid").get("details").get("ALPGBT_VERSION")

## Get lpGBT version from module in DB
def getLpGBTversionFromDB(moduleName):
    if verbose>0: print("Calling getLpGBTversionFromDB()", moduleName)
    module = getModuleFromDB(moduleName)
    if module is None:
        print("ERROR: Could not find module %s in the database."%moduleName)
        raise Exception("Error in calling getLpGBTversionFromDB() for module %s. Module does not exist in the database (see http://pccmslab1.pi.infn.it:5000/static/modules.html)"%(moduleName))
    
    if "children" in module and "lpGBT" in module["children"] and "PS Read-out Hybrid" in module["children"] and "details" in module["children"]["PS Read-out Hybrid"] and "ALPGBT_VERSION" in module["children"]["PS Read-out Hybrid"]["details"]:
        lpGBTversion = module["children"]["PS Read-out Hybrid"]["details"]["ALPGBT_VERSION"]
        if verbose>1: print("Found lpGBT version %s for module %s"%(lpGBTversion, moduleName))
        return lpGBTversion
    else:
        print("[getLpGBTversionFromDB]: Debug info. Module:")
        print(module)
        print()
#        print(module.get("children"))
        print("WARNING - [getLpGBTversionFromDB] - Could not find lpGBT version for module %s in the database. V1 will be used as fallback."%moduleName)
        return "V1"

def getSlotBIFromOpticalGroupAndBoard(connectionMapFC7, og):
    """
    Get the slotBI from the optical group and board.
    slotBI is a number between 0 and 8 (slot in the burn-in).
    Returns: slotBI as an integer, or None if not found
    """
    if verbose>0: print("Calling getSlotBIFromOpticalGroupAndBoard()", fc7, og)
        
    if connectionMapFC7 is None:
        raise Exception("Error in calling getSlotBIFromOpticalGroupAndBoard() for optical group %s. FC7 %s does not exist in the database (see http://pccmslab1.pi.infn.it:5000/static/connections.html)"%(og, fc7))
    
    if verbose>1: print("Looking for 'OG%s'"%og)
    
    # Search through the connection map for the matching optical group
    for el in connectionMapFC7.values():
        if "det_port" in el and el["det_port"].replace(" ", "") == "OG%s"%og:
            if "connections" in el:
                for conn in el["connections"]:
                    if "det_port" in conn and conn["det_port"] == ["fiber"]:
                        if "cable" in conn and conn["cable"].startswith("B"):
                            slotBI = int(conn["cable"].replace("B",""))
                            if verbose>1: print("Found slotBI %s for OG%s in FC7 %s"%(slotBI, og, fc7))
                            return slotBI
    
    print("ERROR [getSlotBIFromOpticalGroupAndBoard]: Could not find any slotBI for optical group %s in FC7 %s"%(og, fc7))
    return None

## print all single module test analyses associated to a session
def printSingleModuleTestAnalysesOfSession(sessionName):
    if verbose>0: print("Calling printSingleModuleTestAnalysesOfSession()", sessionName)
    session = getSessionFromDB(sessionName)
    if session is None:
        print("ERROR: Could not find session %s in the database."%sessionName)
        raise Exception("Error in calling printSingleModuleTestAnalysesOfSession() for session %s. Session does not exist in the database (see http://pccmslab1.pi.infn.it:5000/static/sessions.html)"%(sessionName))
    
    if "test_runName"  in session:
        runs = session["test_runName"]
    else:
        print("ERROR: Could not find 'test_runName' field in session %s in the database."%sessionName)
        raise Exception("Error in calling printSingleModuleTestAnalysesOfSession() for session %s. 'test_runName' field does not exist in the database (see http://pccmslab1.pi.infn.it:5000/static/sessions.html)"%(sessionName))

    for run in runs:
        run = getRunFromDB(run)
        #print(f"Run: {run.get('test_runName', 'unknown')}")
        moduleTests = run.get("moduleTestName", None)
        for moduleTest in moduleTests:
            moduleTest = getModuleTestFromDB(moduleTest)
            print(f"{moduleTest['moduleTestName']} , {run['runDate']}")
            analysisName = moduleTest.get("moduleTestAnalysisName", None)
            if analysisName:
                print(f"- {analysisName}")

### This code allow you to test this code using "python3 databaseTools.py"
if __name__ == '__main__':
    session = "session812"
    print("printSingleModuleTestAnalysesOfSession(%s):"%session)
    printSingleModuleTestAnalysesOfSession(session)
    print("Testing databaseTools.py")
    module = "PS_26_IBA-10003"
    print(f"getLpGBTversionFromDB({module}):", getLpGBTversionFromDB(module))
    print("getFirmwareVersionInFC7OT('FC7OT2'):", getFirmwareVersionInFC7OT("FC7OT2"))
    from datetime import datetime
    now = datetime.now().timestamp()
    print(f"updateFirmwareVersionInFC7OT('FC7OT2', 'databaseToolsTest', {now}):", updateFirmwareVersionInFC7OT("FC7OT2", "databaseToolsTest", now))
    filename = "ModuleTest_settings.xml"
    splitBI_string = "1,2"
    print("Test getOpticaGroupAndBoardFromSlots('%s'):"%splitBI_string, getOpticaGroupAndBoardFromSlots(splitBI_string.split(",")))
    print()
    allModules = getListOfModulesFromDB()
    for mod in allModules:
        print(mod["moduleName"])
    iv_scans = getIVscansOfModule("PS_26_IPG-10010")
    print("IV scans for PS_26_05-IPG_001021:")
    for scan in iv_scans:
        print(scan["sessionName"],scan["runType"], scan["IVScanId"])
    connectionMap = getConnectionMap("PS_26_IPG-10010")
    print(connectionMap)
    saveMapToFile(connectionMap, "connectionMap.json")
    r = getRunFromDB("run303")
    print(r)
    moduleName = "PS_26_IPG-10010"
    testID = "T2023_11_08_17_57_54_302065"
    #testID = "T52"
    hwToModuleName, hwToMongoID = makeModuleNameMapFromDB()

    print("getFiberLink", 'PS_26_IPG-10010')
    pprint(getFiberLink('PS_26_IPG-10010'))

    print("getModuleConnectedToFC7:", "FC7OT2", "OG2")
    pprint(getModuleConnectedToFC7("FC7OT2", "OG2"))

    print("getSlotBIFromOpticalGroupAndBoard:", "FC7OT2", "2")
    connectionMapFC7 = getConnectionMapFromFC7("FC7OT2")
    slot = getSlotBIFromOpticalGroupAndBoard(connectionMapFC7, "2")
    pprint(slot)

    print("getConnectionMapFromModule:", moduleName)
    connectionMap = getConnectionMap(moduleName)
    slot = getSlotBIFromModuleConnectionMap(connectionMap)
    pprint(slot)

    print("\nhwToModuleName:")
    from pprint import pprint
    pprint(hwToModuleName)
    print()
    print("\nhwToMongoID:")
    from pprint import pprint
    pprint(hwToMongoID)
    print()
    
    module = getModuleFromDB(moduleName)
    print("\n #####     Check Module %s on MongoDB    ##### \n"%moduleName)
    pprint(module)
    
    print("\n #####     Check if module %s is 5G or 10G    ##### \n"%moduleName)
    print(getModuleBandwidthFromDB(moduleName))

    test = getTestFromDB(testID)
    print("\n #####     Check Test %s on MongoDB    ##### \n"%testID)
    pprint(test)
