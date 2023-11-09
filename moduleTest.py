"""
alias PythonController.py='python3 /home/thermal/sdonato/Ph2_ACF/pythonUtils/PythonController.py'
alias egrep='egrep --color=auto'
alias fgrep='fgrep --color=auto'
alias formatAll='find /home/thermal/sdonato/Ph2_ACF -type f \( -name "*.cc" -o -name "*.h" \) ! -path "/home/thermal/sdonato/Ph2_ACF/MessageUtils/*" ! -path "/home/thermal/sdonato/Ph2_ACF/*/_deps/*" | xargs /opt/rh/llvm-toolset-7.0/root/usr/bin/clang-format -i'
alias fpgaconfig.py='python3 /home/thermal/sdonato/Ph2_ACF/pythonUtils/fpgaconfig.py'
alias grep='grep --color=auto'
alias julabo_lock-off=' /home/thermal/suvankar/power_supply//simbxcntrl lock-off'
alias julabo_lock-on=' /home/thermal/suvankar/power_supply//simbxcntrl lock-on'
alias julabo_read-sensors=' /home/thermal/suvankar/power_supply//simbxcntrl read-sensors'
alias julabo_set-temperature=' /home/thermal/suvankar/power_supply//setTemperatureJulabo.sh'
alias julabo_switch-off='echo -ne '\''out_mode_05 0\nin_sp_00\nexit\n'\'' | /home/thermal/suvankar/power_supply//runjulabo'
alias julabo_switch-on='echo -ne '\''out_mode_05 1\nin_sp_00\nexit\n'\'' | /home/thermal/suvankar/power_supply//runjulabo'
alias julabo_valve-off=' /home/thermal/suvankar/power_supply//simbxcntrl valve-on'
alias julabo_valve-on=' /home/thermal/suvankar/power_supply//simbxcntrl valve-off'
alias l.='ls -d .* --color=auto'
alias ll='ls -l --color=auto'
alias ls='ls --color=auto'
alias vi='vim'
alias which='alias | /usr/bin/which --tty-only --read-alias --show-dot --show-tilde'
"""

import os, subprocess, requests, ROOT
from pprint import pprint
from datetime import datetime
from PS_Module_settings import config as xmlConfig
from copy import copy, deepcopy

ip="192.168.0.45"
port=5000

verbose=10
skipBurnIn = True
runFpgaConfig = False
useExistingModuleTest = False
useExistingModuleTest = "T2023_11_08_17_57_54_302065" ## read existing module test instead of launching a new test!
skipMongo = False
operator = "Mickey Mouse"
xmlOutput="ModuleTest_settings.xml"
xmlTemplate="PS_Module_template.xml"
firmware="ps_twomod_oct23.bin"

## add these lpGBT IDs to some random modules (it should be defined in the module database)
lpGBTids = ['42949672', '42949673', '42949674', '0x00', '0x67']

### values used for testing
if skipMongo:
    moduleID = "M1234"
#    moduleMongoID = "654a1486b8b3879634268c42"

temps = [2.2,2.4]

def getDateTimeAndTestID():
    date = str(datetime.now())
    testID = "T"+date.replace("-","_").replace(":","_").replace(" ","_").replace(".","_")
    return date, testID


date, testID = getDateTimeAndTestID()

def runCommand(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, executable='/bin/bash'):
    if verbose>2: print(command)
    return subprocess.run(command, check=check, stdout=stdout, stderr=stderr, shell=shell)

#def loadBashRC(location = "/home/thermal/.bashrc"):
#    if verbose>0: print("Calling loadBashRC()")
#    output = runCommand(". %s"%location)
    
def burnIn_lockOn():
    if verbose>0: print("Calling burnIn_lockOn()")
    output = runCommand("/home/thermal/suvankar/power_supply//simbxcntrl lock-on")
    if verbose>1: print(output)

def burnIn_switchOn():
    if verbose>0: print("Calling burnIn_switchOn()")
    output = runCommand("echo -ne '\''out_mode_05 1\nin_sp_00\nexit\n'\'' | /home/thermal/suvankar/power_supply//runjulabo")
    if verbose>1: print(output)

def burnIn_valveOn():
    if verbose>0: print("Calling burnIn_valveOn()")
    output = runCommand("/home/thermal/suvankar/power_supply//simbxcntrl valve-on")
    if verbose>1: print(output)

def burnIn_readSensors():
    if verbose>0: print("Calling burnIn_readSensors()")
    output = runCommand("/home/thermal/suvankar/power_supply//simbxcntrl read-sensors")
    temps = output.stdout.decode().split("buffer: [")[1].split("]\n")[0]
    temps = [float(temp) for temp in temps.split(",")]
    if verbose>1: print(output)
    return temps

def burnIn_setTemperature(temperature):
    if verbose>0: print("Calling burnIn_setTemperature(%f)"%temperature)
    output = runCommand("/home/thermal/suvankar/power_supply//setTemperatureJulabo.sh .3%f"%temperature)
    if verbose>1: print(output)

def fpgaconfig(xmlFile, firmware):
    if verbose>0: print("Calling fpgaconfig()", xmlFile, firmware)
    output = runCommand("fpgaconfig -c %s -i %s"%(xmlFile, firmware))
    if verbose>1: print(output)

def getID(output):
    output = output.stdout.decode() + output.stderr.decode()
    tag_word = "Fused Id is "
    id_pos = output.find(tag_word)
    id_txt = output[id_pos+len(tag_word):id_pos+20]
    id_txt = id_txt.split("\n")[0]
    if not id_txt.isdigit():
        raise Exception("Something wrong in getID() |%s|"%id_txt)
    return id_txt
#    return "654a1486b8b3879634268c42"

def getIDsFromROOT(rootFile, xmlConfig):
    global out
    IDs = {}
    for board_id, board in xmlConfig["boards"].items():
        for opticalGroup_id, opticalGroup in board["opticalGroups"].items():
            objName = "Detector/Board_%s/OpticalGroup_%s/D_B(%s)_InitialLpGBTConfiguration_OpticalGroup(%s);1"%(board_id, opticalGroup_id, board_id, opticalGroup_id)
            out = rootFile.Get(objName)
            if not out: 
                print("WARNING: Missing %s in %s. Skipping."%(objName, rootFile.GetName()))
                IDs[(board_id, opticalGroup_id)] = "-1"
                continue
            IDs[(board_id, opticalGroup_id)] = {}
            out = str(out.GetString()).split("CHIPID registers")[1].split("RegName")[1] ## Select CHIPID section
            for l in out.split("\n"):
                print(l)
                l = l.replace("     "," ").replace("    "," ").replace("   "," ").replace("  "," ")
                l = l.split(" ")
                if len(l)==5:
                    IDs[(board_id, opticalGroup_id)][l[0]]= l[3]
            ## just take "CHIPID0" for the moment
            IDs[(board_id, opticalGroup_id)]= IDs[(board_id, opticalGroup_id)]["CHIPID0"]
    return IDs

def lpGBT_version(fileName):
    id = fileName.split("lpGBT_v")[1].split(".txt")[0]
    if not id.isdigit():
        raise Exception("Something wrong with %s"%opticalGroup["lpGBT"])
    return id

def runModuleTest(xmlFile="PS_Module.xml", logFolder="logs"):
    global output
    if verbose>0: print("Calling runModuleTest()", xmlFile, logFolder)
    date, testID = getDateTimeAndTestID()
    if not useExistingModuleTest:
        logFile = "%s/%s.log"%(logFolder,testID)
    else:
        logFile = "%s/%s.log"%(logFolder,useExistingModuleTest)
    if verbose>0: print(testID,logFile)
    if not useExistingModuleTest:
        output = runCommand("ot_module_test -f %s -t -m -a --reconfigure -b --moduleId %s --readIDs | tee %s"%(xmlFile,testID,logFile)) #or --readlpGBTIDs ?
    else:
        output = runCommand("cat logs/2023_11_08_14_36_06_465927.log | tee %s"%(logFile)) #or --readlpGBTIDs ?
#    hwID = getID(output)
    if verbose>1: print(output)
    return testID, date #, hwID


def makeXml(xmlOutput, xmlConfig, xmlTemplate):
    global BeBoard, connection, board, MPA, SSA, Hybrid
    if verbose>0: print("Calling makeXml()", xmlOutput, xmlTemplate)
    if verbose>2: pprint(xmlConfig)
    from bs4 import BeautifulSoup
    import xml.etree.ElementTree as ET
    tree = ET.parse(xmlTemplate)
    ## Read template
    HwDescription = tree.getroot()
    BeBoard = HwDescription.find("BeBoard")
    connection = BeBoard.find("connection")
    OpticalGroup = BeBoard.find("OpticalGroup")
    lpGBT = OpticalGroup.find("lpGBT")
    Hybrid = OpticalGroup.find("Hybrid")
    SSA = Hybrid.find("SSA")
    MPA = Hybrid.find("MPA")
    for el in [HwDescription, BeBoard, OpticalGroup, lpGBT, Hybrid, SSA, MPA]:
        print(el.getchildren(),el.keys())
    
    ## Clean template from the existing parameters
    Hybrid.remove(SSA)
    Hybrid.remove(MPA)
    OpticalGroup.remove(Hybrid)
    OpticalGroup.remove(lpGBT)
    BeBoard.remove(OpticalGroup)
    BeBoard.remove(connection)
    HwDescription.remove(BeBoard)
    
    ## Make a copy of them
    Hybrid_ = deepcopy(Hybrid)
    OpticalGroup_ = deepcopy(OpticalGroup)
    BeBoard_ = deepcopy(BeBoard)
    
    ## Add back the objects to the xml, using the proper values
    for board_id, board in xmlConfig["boards"].items():
        BeBoard = deepcopy(BeBoard_)
        BeBoard.set("Id", str(board_id))
        connection.set("uri", connection.get("uri").replace("XXXXX",board["ip"]) )
        BeBoard.insert(0, connection)
        for opticalGroup_id, opticalGroup in board["opticalGroups"].items():
            OpticalGroup = deepcopy(OpticalGroup_)
            OpticalGroup.set("Id", str(opticalGroup_id))
            lpGBT.set("Id", lpGBT_version(opticalGroup["lpGBT"]))
            lpGBT.set("version", lpGBT_version(opticalGroup["lpGBT"]))
            lpGBT.set("configfile", opticalGroup["lpGBT"])
            OpticalGroup.insert(1,lpGBT)
            for hybrid_id, hybrid in opticalGroup["hybrids"].items():
                Hybrid = deepcopy(Hybrid_)
                Hybrid.set("Id", str(hybrid_id))
#                BeBoard.insert(2,copy(OpticalGroup))
                SSAFiles_position = Hybrid.getchildren().index(Hybrid.find("SSA_Files"))
#                print(hybrid["pixels"])
#                print(hybrid["strips"])
                if not "strips" in hybrid: hybrid["strips"]=[]
                for strip_id in hybrid["strips"]:
                    SSA.set("Id", str(strip_id))
                    Hybrid.insert(SSAFiles_position+1,deepcopy(SSA))
                    print("Appending", SSA.get("Id"))
                MPAFiles_position = Hybrid.getchildren().index(Hybrid.find("MPA_Files"))
                if not "pixels" in hybrid: hybrid["pixels"]=[]
                for pixel_id in hybrid["pixels"]:
                    MPA.set("Id", str(pixel_id))
                    Hybrid.insert(MPAFiles_position+1,deepcopy(MPA))
                    print("Appending", MPA.get("Id"))
                OpticalGroup.insert(2,deepcopy(Hybrid))
            BeBoard.insert(2,deepcopy(OpticalGroup))
        HwDescription.insert(0,deepcopy(BeBoard))
    tree.write(xmlOutput)
    if verbose>0: print("Created XML %s"%xmlOutput)
    return xmlOutput

allowedChips = ["MPA", "SSA"]
def getMean(rootFile, board_id, opticalGroup_id, hybrid_id, ps_id, chip):
    if not chip in allowedChips: raise Exception("Chip %s now allowed. Allowed chips: %s"%(chip, allowedChips))  
    histoName = "Detector/Board_%s/OpticalGroup_%s/Hybrid_%s/%s_%s/D_B(%s)_O(%s)_H(%s)_NoiseDistribution_Chip(%s)"%(board_id, opticalGroup_id, hybrid_id, chip, ps_id, board_id, opticalGroup_id, hybrid_id, ps_id)
    histo = rootFile.Get(histoName)
    if histo:
        return histo.GetMean(), histoName.split("/")[-1]+chip
    else:
        print("WARNING: Missing %s in %s"%(histoName, rootFile.GetName()))
        return -1, histoName.split("/")[-1]+chip

def getROOTfile(testID):
    matches = [folder for folder in os.listdir("Results") if testID in folder ]
    if len(matches) != 1: raise Exception("%d matches of %s in Result folder. %s"%( len(matches), testID, str(matches)))
    fName = "Results/%s/Hybrid.root"%matches[0]
    return ROOT.TFile.Open(fName)

def getNoise(rootFile, xmlConfig):
    if verbose>0: print("Calling getNoise()", rootFile.GetName())
    noises = {}
    for board_id, board in xmlConfig["boards"].items():
        for opticalGroup_id, opticalGroup in board["opticalGroups"].items():
            for hybrid_id, hybrid in opticalGroup["hybrids"].items():
                for strip_id in hybrid["strips"]:
                    noise, histoName = getMean(rootFile, board_id, opticalGroup_id, hybrid_id, strip_id, "SSA")
                    if histoName in noises: raise Exception("%s is already in noises (getNoise function): %s."%(histoName, noises.keys()))
                    noises[histoName] = noise
                for pixel_id in hybrid["pixels"]:
                    noise, histoName = getMean(rootFile, board_id, opticalGroup_id, hybrid_id, pixel_id, "MPA")
                    if histoName in noises: raise Exception("%s is already in noises (getNoise function): %s."%(histoName, noises.keys()))
                    noises[histoName] = noise

    return noises

def uploadTest(testID, testResult = {}):
    if verbose>0: print("Calling uploadTest()", testID)
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

def getTest(testID):
    if verbose>0: print("Calling getTest()", testID)
    api_url = "http://%s:%d/tests/%s"%(ip, port, testID)
    response = requests.get(api_url)
    if response.status_code == 200:
        if verbose>1: print("Module %supdated successfully")
    else:
        print("Failed to update the module. Status code:", response.status_code)
    return eval(response.content.decode())

def updateModuleTest(updatedTestList, moduleID):
    if not updatedTestList or len(updatedTestList)<1: raise Exception("updatedTestList is empty. " + str(updatedTestList))
    if verbose>0: print("Calling updateModuleTest()", updatedTestList, moduleID)
    api_url = "http://%s:%d/modules/%s"%(ip, port, moduleID)
    updated_module = { "tests": updatedTestList }
    response = requests.put(api_url, json=updated_module)
    if response.status_code == 200:
        if verbose>1: print("Module updated successfully")
    else:
        print("Failed to update the module. Status code:", response.status_code)

def getModule(moduleID=1234):
    if verbose>0: print("Calling getModule()", moduleID)
    api_url = "http://%s:%d/modules/%s"%(ip, port, moduleID)
    response = requests.get(api_url)
    if response.status_code == 200:
        if verbose>1: print("Module updated successfully")
    else:
        print("Failed to update the module. Status code:", response.status_code)
    return eval(response.content.decode().replace("null","[]"))

def makeModuleIdMap():
    if verbose>0: print("Calling makeModuleIdMap()")
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
        hwToModuleID[lpGBTid] = modules[i]["moduleID"]
        hwToMongoID[lpGBTid] = modules[i]["_id"]
    
    ### "-1", ie. missing modules, should go in "-1"
    hwToModuleID["-1"] = "-1"
    hwToMongoID["-1"] = "-1"
    return hwToModuleID, hwToMongoID

xmlFile = makeXml(xmlOutput, xmlConfig, xmlTemplate)

if not skipMongo: 
    hwToModuleID, hwToMongoID = makeModuleIdMap()

if runFpgaConfig: fpgaconfig(xmlFile, firmware)

testID, date = runModuleTest(xmlFile) #, hwID

rootFile = getROOTfile(testID) if not useExistingModuleTest else getROOTfile(useExistingModuleTest) 

if not skipBurnIn: temps = burnIn_readSensors()
IDs = getIDsFromROOT(rootFile, xmlConfig)
print(IDs)
noises = getNoise(rootFile , xmlConfig)

def getResult(noises):
    for noise in noises.values():
        if noise>5 or noise<2:
            return "failed"
    return "pass"

def makeBoardMap(xmlConfig):
    boardMap = {}
    for board_id, board in xmlConfig["boards"].items():
         boardMap[board_id] = board["ip"]
    return boardMap


result = getResult(noises)

board_opticals = list(IDs.keys())

if not skipMongo: 
    moduleIDs = [ hwToModuleID[IDs[bo]] for bo in board_opticals ]
    moduleMongoIDs = [ hwToMongoID[IDs[bo]] for bo in board_opticals ]

if not skipMongo: 
    testResult = { ##see https://github.com/pisaoutertracker/testmongo/blob/f7e032c3dafa7954f834810903ea8ac9dc5bdbd0/populate_db.py#L70C6-L70C8
            "testID": testID,
            "modules_list": moduleMongoIDs,
            "testType": "Type1",
            "testDate": date,
            "testOperator": operator,
            "testStatus": "completed",
            "testResults": {
                "result": result,
                "noises": noises,
                "boards": makeBoardMap(xmlConfig),
                "temperatures": temps,
                "xmlConfig": xmlConfig
            },
    #        ## Not manadatory
    }

    uploadTest(
        testID = testID,
        testResult = testResult,
    )

    print("\n #####     Check Test %s on MongoDB    ##### \n"%testID)
    test = getTest(testID = testID)
    pprint(test)

    for moduleID in moduleIDs:
        if moduleID == "-1": 
            print("\n WARNING: Skipping missing (crashing) module.")
            continue
        module = getModule(moduleID = moduleID)

        print("\n #####     Check Module %s on MongoDB - before    ##### \n"%moduleID)
        pprint(module)

        ### Add test to the modules database ###
        if not test["_id"] in module["tests"]:
            updatedTestList = module["tests"]
            updatedTestList.append(test["_id"])
            updateModuleTest( 
                moduleID = moduleID, 
                updatedTestList = updatedTestList
            )
            print("\n #####     Check Module %s on MongoDB - after     ##### \n"%moduleID)
            pprint(getModule(moduleID = moduleID))
        elif not useExistingModuleTest:
            raise Exception("Test %s (%s) is already included in %s (%s) test list %s."%(test["testID"], test["_id"], module["moduleID"], module["_id"], module["tests"]))
        else:
            print("Warning: Test %s (%s) is already included in %s (%s) test list %s."%(test["testID"], test["_id"], module["moduleID"], module["_id"], module["tests"]))
            print("It is not a problem because you are using the 'useExistingModuleTest' option.")
    

