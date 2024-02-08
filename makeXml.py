from moduleTest import verbose

# Get "0/1" from "lpGBT_v0/1.txt"

def lpGBT_version(fileName):
    id = fileName.split("lpGBT_v")[1].split(".txt")[0]
    if not id.isdigit():
        raise Exception("Something wrong with %s"%opticalGroup["lpGBT"])
    return id

#

## make PS_Module_settings.py from already existing ROOT file (necessary to upload old tests)

def makeConfigFromROOTfile(fileName):
    from ROOT import TFile
    ROOTfile = TFile.Open(fileName)
    xmlConfig = {
        "commonSettings" : "fake",
        "Nevents" : "-1",
        "boards" : {}
    }
    for objB in ROOTfile.Get("Detector").GetListOfKeys(): 
        objB_ = objB.GetName()
        if "Board_" in objB_:
            board_id = objB_.split("Board_")[1]
            if not board_id in xmlConfig["boards"]: 
                xmlConfig["boards"][board_id] = {"ip" : "fake", "opticalGroups" : {}}
            for objO in ROOTfile.Get("Detector/%s"%objB_).GetListOfKeys(): 
                objO_ = objO.GetName()
                if "OpticalGroup_" in objO_:
                    optical_id = objO_.split("OpticalGroup_")[1]
                    if not optical_id in xmlConfig["boards"][board_id]["opticalGroups"]: 
                        xmlConfig["boards"][board_id]["opticalGroups"][optical_id] = {"lpGBT" : "fake", "hybrids" : {}}
                    for objH in ROOTfile.Get("Detector/%s/%s"%(objB_, objO_)).GetListOfKeys(): 
                        objH_ = objH.GetName()
                        if "Hybrid_" in objH_:
                            hybrid_id = objH_.split("Hybrid_")[1]
                            hybrid_id_fixed = int(hybrid_id) - int(optical_id)*2
                            hybrid_id_fixed = str(hybrid_id_fixed)
                            if not hybrid_id_fixed in xmlConfig["boards"][board_id]["opticalGroups"][optical_id]["hybrids"]: 
                                xmlConfig["boards"][board_id]["opticalGroups"][optical_id]["hybrids"][hybrid_id_fixed] = {"strips" : [], "pixels" : []}
                            for objPS in ROOTfile.Get("Detector/%s/%s/%s"%(objB_, objO_, objH_)).GetListOfKeys(): 
                                objPS_ = objPS.GetName()
                                hybrid = xmlConfig["boards"][board_id]["opticalGroups"][optical_id]["hybrids"][hybrid_id_fixed]
                                if "SSA" in objPS_:
                                    hybrid["strips"].append(int(objPS_.split("SSA_")[1]))
                                if "MPA" in objPS_:
                                    hybrid["pixels"].append(int(objPS_.split("MPA_")[1]))
    return xmlConfig

# Create the XML file - to be used in the ot_module_test - reading the configuration defined in xmlConfig (PS_Module_settings.py)

def makeXml(xmlOutput, xmlConfig, xmlTemplate):
    legacyVersion = False
    if "v0" in xmlTemplate: legacyVersion = True
    global BeBoard, connection, board, MPA, SSA, Hybrid, tree
    if verbose>0: print("Calling makeXml()", xmlOutput, xmlTemplate)
    from pprint import pprint
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
    if not legacyVersion:
        SSA = Hybrid.find("SSA2")
        MPA = Hybrid.find("MPA2")
    else:
        SSA = Hybrid.find("SSA")
        MPA = Hybrid.find("MPA")
    if verbose > 5:
        for el in [HwDescription, BeBoard, OpticalGroup, lpGBT, Hybrid, SSA, MPA]:
            print(el)
            print(list(el),el.keys())
    
    ## Clean template from the existing parameters
    Hybrid.remove(SSA)
    Hybrid.remove(MPA)
    OpticalGroup.remove(Hybrid)
    OpticalGroup.remove(lpGBT)
    BeBoard.remove(OpticalGroup)
    BeBoard.remove(connection)
    HwDescription.remove(BeBoard)
    
    ## Make a copy of them
    from copy import deepcopy
    Hybrid_ = deepcopy(Hybrid)
    OpticalGroup_ = deepcopy(OpticalGroup)
    BeBoard_ = deepcopy(BeBoard)
    
    ## Add back the objects to the xml, using the proper values
    for board_id, board in sorted(xmlConfig["boards"].items(), reverse=True):
        BeBoard = deepcopy(BeBoard_)
        BeBoard.set("Id", str(board_id))
        connection.set("uri", connection.get("uri").replace("XXXXX",board["ip"]) )
        BeBoard.insert(0, connection)
        for opticalGroup_id, opticalGroup in sorted(board["opticalGroups"].items(), reverse=True):
            OpticalGroup = deepcopy(OpticalGroup_)
            OpticalGroup.set("Id", str(opticalGroup_id))
#            lpGBT.set("Id", lpGBT_version(opticalGroup["lpGBT"])) ## keep it to 0
            lpGBT.set("version", lpGBT_version(opticalGroup["lpGBT"]))
            lpGBT.set("configfile", opticalGroup["lpGBT"])
            OpticalGroup.insert(1,lpGBT)
            for hybrid_id, hybrid in sorted(opticalGroup["hybrids"].items(), reverse=True):
                Hybrid = deepcopy(Hybrid_)
                Hybrid.set("Id", str(hybrid_id))
                SSAFiles_position = list(Hybrid).index(Hybrid.find("SSA_Files"))
                if not "strips" in hybrid: hybrid["strips"]=[]
                for strip_id in sorted(hybrid["strips"], reverse=True):
                    SSA.set("Id", str(strip_id))
                    Hybrid.insert(SSAFiles_position+1,deepcopy(SSA))
                MPAFiles_position = list(Hybrid).index(Hybrid.find("MPA_Files"))
                if not "pixels" in hybrid: hybrid["pixels"]=[]
                for pixel_id in sorted(hybrid["pixels"], reverse=True):
                    MPA.set("Id", str(pixel_id))
                    Hybrid.insert(MPAFiles_position+1,deepcopy(MPA))
                OpticalGroup.insert(2,deepcopy(Hybrid))
            BeBoard.insert(2,deepcopy(OpticalGroup))
        HwDescription.insert(0,deepcopy(BeBoard))
    ## Modify  Nevents setting if it is defined in the python config
    if "Nevents" in xmlConfig:
        Nevents = int(xmlConfig["Nevents"])
        for setting in list(tree.find("Settings")):
            if Nevents>0 and setting.get("name") == "Nevents":
                setting.text = str(Nevents)
    tree.write(xmlOutput)
    if verbose>0: print("Created XML %s"%xmlOutput)
    return xmlOutput

# Read a string ("PS_Module_settings.py") and return the dictionary contained in that file

def readXmlConfig(xmlConfigFile, folder="."):
    import sys
    pwd = sys.path[0]
    sys.path.remove(pwd)
    sys.path.append(folder)
    import importlib
    PS_Module_settings = xmlConfigFile[:-3] ## drop .py from "PS_Module_settings.py"
    PS_Module_settings = importlib.import_module(PS_Module_settings)
    xmlConfig = PS_Module_settings.config
    sys.path.insert(0, pwd)
    sys.path.remove(folder)
    return xmlConfig

# Make a map containing the FC7 used in each board (eg. boardMap[1] = "fc7ot3:5001")

#def makeBoardMap(xmlConfig):
#    boardMap = {}
#    for board_id, board in xmlConfig["boards"].items():
#         boardMap[int(board_id)] = board["ip"]
#    return boardMap

## Make a map containing the module used in each board/optical (eg. {'fc7ot2_optical0' : ("M123", 67)})

#def makeModuleMap(xmlConfig, IDs, hwToModuleID):
#    moduleMap = dict()
##    for b
#    for id in IDs: ## id[0] = board number, id[1] = optical group number
#        fc7 = xmlConfig["boards"][id[0]]["ip"] ##get fc7ot3:50001
#        fc7 = fc7.split(":")[0] #keep fc7ot3
#        hwId = IDs[id]
#        moduleMap["%s_optical%s"%(fc7, id[1])] = (hwToModuleID[hwId], int(hwId))
#    return moduleMap

## Make a map containing the module chip used in each module (eg. {67 : ("SSA0": 4.348, "MPA9": 2.348,)})

def makeNoiseMap(xmlConfig, noisePerChip, IDs, hwToModuleID):
    boardMap = dict() ## boardMap[1] = "fc7ot3:5001"
    moduleMap = dict() ## moduleMap['fc7ot2_optical0'] = ("M123", 67)
    noiseMap = dict() ## noiseMap[749637543]["H1SSA7"] = 1.3156
    for board_id, board in xmlConfig["boards"].items():
        board_id = int(board_id)
        fc7 = board["ip"] ##get fc7ot3:50001
        fc7 = fc7.split(":")[0] #keep fc7ot3
        boardMap[board_id] = fc7
        for opticalGroup_id, opticalGroup in board["opticalGroups"].items():
            opticalGroup_id = int(opticalGroup_id)
            hwId = IDs[(board_id, opticalGroup_id)] if (board_id, opticalGroup_id) else -1
            moduleMap['%s_optical%s'%(fc7, opticalGroup_id)] = (hwToModuleID[hwId], hwId)
            noiseMap[hwId] = {}
            for hybrid_id, hybrid in sorted(opticalGroup["hybrids"].items()):
                hybrid_id = int(hybrid_id)
                hybrid_plus_opt = str(int(opticalGroup_id)*2 + int(hybrid_id))
                for strip_id in sorted(hybrid["strips"]):
                    strip_id = int(strip_id)
                    noiseMap[hwId]["H%s_SSA%s"%(hybrid_id, strip_id)] = noisePerChip['D_B(%s)_O(%s)_H(%s)_NoiseDistribution_Chip(%s)SSA'%(board_id, opticalGroup_id, hybrid_plus_opt, strip_id)]
                for pixel_id in sorted(hybrid["pixels"]):
                    pixel_id = int(pixel_id)
                    noiseMap[hwId]["H%s_MPA%s"%(hybrid_id, pixel_id)] = noisePerChip['D_B(%s)_O(%s)_H(%s)_NoiseDistribution_Chip(%s)MPA'%(board_id, opticalGroup_id, hybrid_plus_opt, pixel_id)]
    return boardMap, moduleMap, noiseMap
    

#  'D_B(0)_O(0)_H(0)_NoiseDistribution_Chip(14)MPA': 2.7255240752051275,
#    for id in IDs: ## id[0] = board number, id[1] = optical group number
#        fc7 = xmlConfig["boards"][id[0]]["ip"] ##get fc7ot3:50001
#        fc7 = fc7.split(":")[0] #keep fc7ot3
#        hwId = IDs[id]
#        moduleMap["%s_optical%s"%(fc7, id[1])] = (hwToModuleID[hwId], int(hwId))

#            'runNoise' : makeNoiseMap(xmlConfig, noisePerChip, hwToModuleID)
#            {
#                67 : {
#                    "SSA0": 4.348,
#                    "SSA4": 3.348,
#                    "MPA9": 2.348,
#                },
#                68 : {
#                    "SSA0": 3.348,
#                    "SSA1": 3.648,
#                },
#                69 : {
#                    "SSA0": 3.548,
#                    "SSA4": 3.248,
#                }

### This code allows you to make the XML file directly with "python3 makeXml.py"

if __name__ == '__main__':
#    verbose = -1
    xmlConfigFile = "PS_Module_settings_test.py"
    xmlOutput="ModuleTest_settings_test.xml"
    xmlTemplate="PS_Module_template.xml"
    print("\nReading %s"%xmlConfigFile)
    xmlConfig = readXmlConfig(xmlConfigFile)
    print("\nxmlConfig:")
    from pprint import pprint
    pprint(xmlConfig)
    print()
    makeXml(xmlOutput, xmlConfig, xmlTemplate)
    print("XML created in %s."%xmlOutput)
    print()
    print("Launch the test with:")
    print("python3 makeXml.py && ot_module_test -f %s -t -m -a --reconfigure -b --moduleId test --readIDs"%xmlOutput)
