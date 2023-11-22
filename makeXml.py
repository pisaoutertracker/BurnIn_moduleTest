from moduleTest import verbose

# Get "0/1" from "lpGBT_v0/1.txt"

def lpGBT_version(fileName):
    id = fileName.split("lpGBT_v")[1].split(".txt")[0]
    if not id.isdigit():
        raise Exception("Something wrong with %s"%opticalGroup["lpGBT"])
    return id

# Create the XML file - to be used in the ot_module_test - reading the configuration defined in xmlConfig (PS_Module_settings.py)

def makeXml(xmlOutput, xmlConfig, xmlTemplate):
    legacyVersion = False
    if "v0" in xmlTemplate: legacyVersion = True
    global BeBoard, connection, board, MPA, SSA, Hybrid
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
    from copy import deepcopy
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
                SSAFiles_position = Hybrid.getchildren().index(Hybrid.find("SSA_Files"))
                if not "strips" in hybrid: hybrid["strips"]=[]
                for strip_id in hybrid["strips"]:
                    SSA.set("Id", str(strip_id))
                    Hybrid.insert(SSAFiles_position+1,deepcopy(SSA))
                MPAFiles_position = Hybrid.getchildren().index(Hybrid.find("MPA_Files"))
                if not "pixels" in hybrid: hybrid["pixels"]=[]
                for pixel_id in hybrid["pixels"]:
                    MPA.set("Id", str(pixel_id))
                    Hybrid.insert(MPAFiles_position+1,deepcopy(MPA))
                OpticalGroup.insert(2,deepcopy(Hybrid))
            BeBoard.insert(2,deepcopy(OpticalGroup))
        HwDescription.insert(0,deepcopy(BeBoard))
    tree.write(xmlOutput)
    if verbose>0: print("Created XML %s"%xmlOutput)
    return xmlOutput

# Read a string ("PS_Module_settings.py") and return the dictionary contained in that file

def readXmlConfig(xmlConfigFile):
    import importlib
    PS_Module_settings = xmlConfigFile[:-3] ## drop .py from "PS_Module_settings.py"
    PS_Module_settings = importlib.import_module(PS_Module_settings)
    xmlConfig = PS_Module_settings.config
    return xmlConfig

# Make a map containing the FC7 used in each board (eg. boardMap[1] = "fc7ot3:5001")

def makeBoardMap(xmlConfig):
    boardMap = {}
    for board_id, board in xmlConfig["boards"].items():
         boardMap[board_id] = board["ip"]
    return boardMap

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
