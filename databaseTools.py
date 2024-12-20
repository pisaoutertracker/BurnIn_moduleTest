from moduleTest import verbose, ip, port, lpGBTids
from pprint import pprint
import requests

def evalMod(string):
    string = string.replace("true","True").replace("false","False")
    return eval(string)

#verbose = 0
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
        if "connections" in out[link]:
            if out[link]["det_port"]==og and len(out[link]["connections"])>0:
                last = out[link]["connections"][-1]
                ## expect 2 "fiber" pointing to the same FC7 and optical group
                if moduleName: assert(moduleName==last["cable"]) 
                moduleName = last["cable"]
        else:
            if "error" in out[link]: print(out[link]["error"])
            #it might be a new module to be added into the database
            #raise Exception("Error in Calling getModuleConnectedToFC7()",fc7, og)
    return moduleName


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
        if verbose>1: print("Module added successfully")
    else:
        print("Failed to add the module. Status code:", response.status_code)
    return response.status_code

def appendAnalysisToModule(analysisName):
    if verbose>0: print("Calling appendAnalysisToModule()")
    api_url = "http://%s:%d/addAnalysis"%(ip, port)
    json = {'moduleTestAnalysisName': analysisName}
    response = requests.get(api_url, params=json)
    print(response)
    print(response.content.decode())
    print(response.status_code)
    if response.status_code == 200:
        if verbose>1: print("Module added successfully")
    else:
        print("Failed to add the module. Status code:", response.status_code)
    return response.status_code

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
        if "hwId" in module:
            hwId = int(module["hwId"])
            hwToModuleName[hwId] = module["moduleName"]
            hwToMongoID[hwId] = module["_id"]
    
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
    print("AAAAA")
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
    r = getRunFromDB("run303")
    print(r)
    moduleName = "M123"
    testID = "T2023_11_08_17_57_54_302065"
    #testID = "T52"
    hwToModuleName, hwToMongoID = makeModuleNameMapFromDB()

    print("getFiberLink", 'PS_26_05-IPG_00102')
    pprint(getFiberLink('PS_26_05-IPG_00102'))

    print("getModuleConnectedToFC7:", "FC7OT2", "0")
    pprint(getModuleConnectedToFC7("FC7OT2", "0"))
       
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
    
    test = getTestFromDB(testID)
    print("\n #####     Check Test %s on MongoDB    ##### \n"%testID)
    pprint(test)

