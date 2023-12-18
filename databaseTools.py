from moduleTest import verbose, ip, port, lpGBTids
from pprint import pprint
import requests

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
    if verbose>2: pprint(newRun)
   
    # URL of the API endpoint for updating a module
    api_url = "http://%s:%d/addRun"%(ip, port)
    
    # Send a PUT request
    response = requests.post(api_url, json=newRun)
    
    # Check the response
    if response.status_code == 201:
        if verbose>1: print("Run uploaded successfully")
    else:
        print("Failed to update the run. Status code:", response.status_code)
        print("response = requests.post(api_url, json=newRun)")
        print(api_url)
        print(newRun)

### read the test result from DB

def getTestFromDB(testID):
    if verbose>0: print("Calling getTestFromDB()", testID)
    api_url = "http://%s:%d/tests/%s"%(ip, port, testID)
    response = requests.get(api_url)
    if response.status_code == 200:
        if verbose>1: print("Module read successfully")
    else:
        print("Failed to update the module. Status code:", response.status_code)
    return eval(response.content.decode())

### read the module test result from DB

def getModuleTestFromDB(testID):
    if verbose>0: print("Calling getModuleTestFromDB()", testID)
    api_url = "http://%s:%d/module_test/%s"%(ip, port, testID)
    response = requests.get(api_url)
    if response.status_code == 200:
        if verbose>1: print("Module test read successfully")
    else:
        print("Failed to update the module. Status code:", response.status_code)
    return eval(response.content.decode())

### get run from DB

def getRunFromDB(testID):
    if verbose>0: print("Calling getRunFromDB()", testID)
    api_url = "http://%s:%d/test_run/%s"%(ip, port, testID)
    response = requests.get(api_url)
    if response.status_code == 200:
        if verbose>1: print("Module read successfully")
    else:
        print("Failed to update the module. Status code:", response.status_code)
    return eval(response.content.decode())

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


new_test = {
    "testID": "T001",
    "modules_list": ["M1", "M2"],
    "testType": "Type1",
    "testDate": "2023-11-01",
    "testStatus": "completed",
    "testResults": {}
}

def addTestToModuleDBNew():
    if verbose>0: print("Calling addTestToModuleDBNew()")
    api_url = "http://%s:%d/addTest"%(ip, port)
    response = requests.put(api_url, json=new_test)
    if response.status_code == 201:
        if verbose>1: print("Module added successfully")
    else:
        print("Failed to add the module. Status code:", response.status_code)

### read a module from DB, given the moduleName

def getModuleFromDB(moduleName=1234):
    if verbose>0: print("Calling getModuleFromDB()", moduleName)
    api_url = "http://%s:%d/modules/%s"%(ip, port, moduleName)
    response = requests.get(api_url)
    if response.status_code == 200:
        if verbose>1: print("Module read successfully")
    else:
        print("Failed to update the module. Status code:", response.status_code)
    return eval(response.content.decode().replace("null","[]"))

### create the maps hwTomoduleName and hwToMongoID to convert the hardware lpGBT ID to module ID and mongo ID.
# -1 = missing module (module didn't work during the test)

def makeModuleNameMapFromDB():
    if verbose>0: print("Calling makeModuleNameMapFromDB()")
    api_url = "http://%s:%d/modules"%(ip, port)
    response = requests.get(api_url)
    modules = eval(response.content.decode().replace("null","[]"))
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
if __name__ == '__main__':
    moduleName = "M123"
    testID = "T2023_11_08_17_57_54_302065"
    #testID = "T52"
    hwToModuleName, hwToMongoID = makeModuleNameMapFromDB()

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
    
    addTestToModuleDBNew()
