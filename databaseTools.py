from moduleTest import verbose, ip, port, lpGBTids
from pprint import pprint
import requests

def evalMod(string):
    string = string.replace("true","True").replace("false","False").replace("null","None")
    return eval(string)

verbose = 10
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
        print("Failed to update the module. Status code:", response.status_code)

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
    print("AAAAA")
    print(response)
    
    # Check the response
    if response.status_code == 201:
        if verbose>1: print("Run uploaded successfully")
    else:
        print("Failed to update the run. Status code:", response.status_code)
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
    response = requests.get(api_url)
    if response.status_code == 200:
        if verbose>1: print("Module read successfully")
    else:
        print("Failed to update the module. Status code:", response.status_code)
    return evalMod(response.content.decode())

### read the fiber connections of slot X

def getFiberLink(slot):
    if verbose>0: print("Calling getFiberLink()", slot)
    api_url = "http://%s:%d/snapshot"%(ip, port)
    
    snapshot_data = {
        "cable": slot,
        "side": "crateSide"
    }
    response = requests.post(api_url, json=snapshot_data)
    
    if response.status_code == 200:
        if verbose>1: print("Module read successfully")
    else:
        print("Failed to update the module. Status code:", response.status_code)
    out = evalMod(response.content.decode())
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
    else:
        print("Failed to update the module. Status code:", response.status_code)
    out = evalMod(response.content.decode())
    return out

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
        print("Failed to update the module. Status code:", response.status_code)
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
        print("Error: Could not find module connected to FC7 %s and optical group %s"%(fc7, og))
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
        print("Failed to update the module. Status code:", response.status_code)
    return evalMod(response.content.decode())

### read the list of modules

def getListOfModulesFromDB():
    if verbose>0: print("Calling getListOfModulesFromDB()")
    api_url = "http://%s:%d/modules"%(ip, port)
    response = requests.get(api_url)
    if response.status_code == 200:
        if verbose>1: print("Session read successfully")
    else:
        print("Failed to update the module. Status code:", response.status_code)
    return evalMod(response.content.decode())


### read the test modules analysis

def getListOfAnalysisFromDB():
    if verbose>0: print("Calling getListOfAnalysisFromDB()")
    api_url = "http://%s:%d/module_test_analysis"%(ip, port)
    response = requests.get(api_url)
    if response.status_code == 200:
        if verbose>1: print("Session read successfully")
    else:
        print("Failed to update the module. Status code:", response.status_code)
    return evalMod(response.content.decode())

### read the module test result from DB

def getSessionFromDB(testID):
    if verbose>0: print("Calling getSessionFromDB()", testID)
    api_url = "http://%s:%d/sessions/%s"%(ip, port, testID)
    response = requests.get(api_url)
    if response.status_code == 200:
        if verbose>1: print("Session read successfully")
    else:
        print("Failed to update the module. Status code:", response.status_code)
    return evalMod(response.content.decode())

### read the module test result from DB

def getModuleTestFromDB(testID):
    if verbose>0: print("Calling getModuleTestFromDB()", testID)
    api_url = "http://%s:%d/module_test/%s"%(ip, port, testID)
    response = requests.get(api_url)
    if response.status_code == 200:
        if verbose>1: print("Module test read successfully")
    else:
        print("Failed to update the module. Status code:", response.status_code)
    return evalMod(response.content.decode())

### get run from DB

def getRunFromDB(testID):
    if verbose>0: print("Calling getRunFromDB()", testID)
    api_url = "http://%s:%d/test_run/%s"%(ip, port, testID)
    response = requests.get(api_url)
    if response.status_code == 200:
        if verbose>1: print("Module read successfully")
    else:
        print("Failed to update the module. Status code:", response.status_code)
    return evalMod(response.content.decode())

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
        print("Failed to update the module. Status code:", response.status_code)

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
        print("Failed to add the module. Status code:", response.status_code)
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
        print("Failed to add the module. Status code:", response.status_code)
    return response.status_code

## check if the expected modules match the modules declared in the database for the slots
def checkIfExpectedModulesMatchModulesInDB(board, slots, modules, args):
    from databaseTools import getModuleConnectedToFC7, getModuleBandwidthFromDB
    for i, slot in enumerate(slots):
        error = None
        moduleFromDB = getModuleConnectedToFC7(board.upper(), "OG%s"%slot)
        if modules[i] == "auto":  
            modules[i] = moduleFromDB
            print("You selected 'auto' for the module in board %s and slot %s. I will use the module %s declared in the connection database."%(board, slot, moduleFromDB))
        moduleFromCLI = modules[i]
        print("board %s, slot %s, moduleFromDB %s, moduleFromCLI %s"%(board, slot, moduleFromDB, moduleFromCLI))
        moduleBandwidth = getModuleBandwidthFromDB(moduleFromCLI)
        print("Expected module %s. According to Pisa db is %s"%(moduleFromCLI, moduleBandwidth))
        if moduleBandwidth == "5Gbps" and args.g10:
            raise Exception("Module %s is declared in the database as 5Gbps, but you are trying to run the test with 10Gbps firmware."%moduleFromDB)
        elif moduleBandwidth == "10Gbps" and args.g5:
            raise Exception("Module %s is declared in the database as 10Gbps, but you are trying to run the test with 5Gbps firmware."%moduleFromDB)
        if moduleFromDB == None:
            from databaseTools import getFiberLink
            fc7, og = getFiberLink(moduleFromCLI)
            if fc7 == None:
                print("No module declared in the database for board %s and slot %s."%(board.upper(), "OG%s"%slot))
                if args.addNewModule:
                    print("It is ok, as you are going to add new modules to the database.")
                else: 
                    error = "No module declared in the database for board %s and slot %s. If you are not adding a new module, something is wrong. If you want to add a new module, please use --addNewModule option."%(board.upper(), "OG%s"%slot)
                    print(error)
            else:
                error = "Module %s is already in the connection database and it is expected in board %s and slot %s, not in board %s and slot %s. You can avoid this error using --ignoreConnection option."%(moduleFromCLI, fc7, og, board.upper(), "OG%s"%slot)
                print(error)
        else:
            if moduleFromDB != moduleFromCLI:
                error = "Module %s declared in the database for board %s and slot %s does not match the module declared in the command line (%s)."%(moduleFromDB, board, slot, modules[i])
                print(error)
            else:
                print("Module %s declared in the database for board %s and slot %s matches the module declared in the command line (%s)."%(moduleFromDB, board, slot, modules[i]))
        if error: 
            if args.ignoreConnection:
                print("WARNING: --ignoreConnection option is active. I will not throw exception if there is a mismatch between the database connection and the module declared.")
                print("WARNING: %s"%error)
            else:
                raise Exception(error+" You can skip this error using --ignoreConnection flag.")
    return

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
        print("Failed to add the session. Status code:", response.status_code)
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
        print("Failed to update the module. Status code:", response.status_code)
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
    print(response)
    print(response.json())
    
    # Check the response
    if response.status_code == 201:
        if verbose>1: print("Module %s uploaded successfully (hwId=%d)"%(moduleName, id_))
    else:
        print("Failed to update the run. Status code:", response.status_code)
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
    


### This code allow you to test this code using "python3 databaseTools.py"
if __name__ == '__main__':
    allModules = getListOfModulesFromDB()
    for mod in allModules:
        print(mod["moduleName"])
    connectionMap = getConnectionMap("PS_26_05-IPG_001021")
    print(connectionMap)
    saveMapToFile(connectionMap, "connectionMap.json")
    r = getRunFromDB("run303")
    print(r)
    moduleName = "PS_26_IPG-10005"
    testID = "T2023_11_08_17_57_54_302065"
    #testID = "T52"
    hwToModuleName, hwToMongoID = makeModuleNameMapFromDB()

    print("getFiberLink", 'PS_26_05-IPG_00102')
    pprint(getFiberLink('PS_26_05-IPG_00102'))

    print("getModuleConnectedToFC7:", "FC7OT2", "OG10")
    pprint(getModuleConnectedToFC7("FC7OT2", "OG10"))
       
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

