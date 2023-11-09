from moduleTest import verbose, ip, port, lpGBTids
from pprint import pprint
import requests

### upload the test result to the "tests" DB

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

### read the test result from DB

def getTestFromDB(testID):
    if verbose>0: print("Calling getTestFromDB()", testID)
    api_url = "http://%s:%d/tests/%s"%(ip, port, testID)
    response = requests.get(api_url)
    if response.status_code == 200:
        if verbose>1: print("Module %supdated successfully")
    else:
        print("Failed to update the module. Status code:", response.status_code)
    return eval(response.content.decode())

### update the "tests" parameter of module in DB using updatedTestList 

def addTestToModuleDB(updatedTestList, moduleID):
    if not updatedTestList or len(updatedTestList)<1: raise Exception("updatedTestList is empty. " + str(updatedTestList))
    if verbose>0: print("Calling addTestToModuleDB()", updatedTestList, moduleID)
    api_url = "http://%s:%d/modules/%s"%(ip, port, moduleID)
    updated_module = { "tests": updatedTestList }
    response = requests.put(api_url, json=updated_module)
    if response.status_code == 200:
        if verbose>1: print("Module updated successfully")
    else:
        print("Failed to update the module. Status code:", response.status_code)

### read a module from DB, given the moduleID

def getModuleFromDB(moduleID=1234):
    if verbose>0: print("Calling getModuleFromDB()", moduleID)
    api_url = "http://%s:%d/modules/%s"%(ip, port, moduleID)
    response = requests.get(api_url)
    if response.status_code == 200:
        if verbose>1: print("Module updated successfully")
    else:
        print("Failed to update the module. Status code:", response.status_code)
    return eval(response.content.decode().replace("null","[]"))

### create the maps hwToModuleID and hwToMongoID to convert the hardware lpGBT ID to module ID and mongo ID.
# -1 = missing module (module didn't work during the test)

def makeModuleIdMapFromDB():
    if verbose>0: print("Calling makeModuleIdMapFromDB()")
    api_url = "http://%s:%d/modules"%(ip, port)
    response = requests.get(api_url)
    modules = eval(response.content.decode().replace("null","[]"))
    hwToModuleID = {} ## hwId --> moduleId
    hwToMongoID = {} ## hwId --> mongoId
    for module in modules:
        hwId = module["_id"] ## to be replaced with the actual hwId from DAQ --readlpGBTIDs 
        hwToModuleID[hwId] = module["moduleID"]
        hwToMongoID[hwId] = module["_id"]
    
    ### hard-code some modules, waiting to have these numbers in the database
    for i, lpGBTid in enumerate(lpGBTids):
        if not lpGBTid in hwToModuleID: hwToModuleID[lpGBTid] = modules[i]["moduleID"]
        if not lpGBTid in hwToMongoID: hwToMongoID[lpGBTid] = modules[i]["_id"]
    
    ### "-1", ie. missing modules, should go in "-1"
    hwToModuleID["-1"] = "-1"
    hwToMongoID["-1"] = "-1"
    return hwToModuleID, hwToMongoID

