### Default values 
verbose = 1000
#sessionName = 'session1'
xmlPyConfigFile = "PS_Module_settings.py"
ip="192.168.0.45"
port=5000
xmlOutput="ModuleTest_settings.xml"
xmlTemplate="PS_Module_template.xml"
firmware_5G="ps_twomod_oct23.bin" ##5 GBps
firmware_10G="ps8m10gcic2l12octal8tlu.bin" ## "ps8m10gcic2l12octa.bin" ##10 GBps
runFpgaConfig = False ## it will run automatically if necessary
## command used to launch commands through Docker (podman)
## -v /home/thermal/suvankar/power_supply/:/home/thermal/suvankar/power_supply/
podmanCommand = 'podman run  --rm -ti -v $PWD/Results:/home/cmsTkUser/Ph2_ACF/Results/:z -v $PWD/logs:/home/cmsTkUser/Ph2_ACF/logs/:z -v $PWD:$PWD:z -v /etc/hosts:/etc/hosts -v ~/private/webdav.sct:/root/private/webdav.sct:z  --net host  --entrypoint bash  gitlab-registry.cern.ch/cms-pisa/pisatracker/pisa_module_test:ph2_acf_v5-01 -c "%s"' ## For older version: docker.io/sdonato/pisa_module_test:ph2_acf_v4-23
import os
prefixCommand = 'cd /home/cmsTkUser/Ph2_ACF && source setup.sh && cd %s' %os.getcwd()
settingFolder = "/home/cmsTkUser/Ph2_ACF/settings"

## assign these lpGBT hardware IDs to some random modules (they will be in the module database)
#lpGBTids = ['3962125297', '42949672', '42949673', '42949674', '2762808384', '0x00', '0x67']
lpGBTids = []

### webdav keys
hash_value_location = "~/private/webdav.sct" #echo "xxxxxxxxxxxxxxx|xxxxxxxxxxxxxxx" > ~/private/webdav.sct
webdav_url = "https://cernbox.cern.ch/remote.php/dav/public-files"
from webdavclient import WebDAVWrapper
hash_value_read, hash_value_write = open(os.path.expanduser(hash_value_location)).read()[:-1].split("\n")[0].split("|")
webdav_wrapper = WebDAVWrapper(webdav_url, hash_value_read, hash_value_write)

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Script used to launch the test of the Phase-2 PS module, using Ph2_ACF. More info at https://github.com/pisaoutertracker/BurnIn_moduleTest. \n Example: \npython3 moduleTest.py --module PS_26_05-IBA_00102 --slot 0,1 --session session1 . ')
    required = parser.add_argument_group('required arguments')
    required.add_argument('--session', type=str, help='Name of the session (eg. session1). ', required=True)
    required.add_argument('--module', type=str,  help='Optical group number (eg. PS_26_05-IBA_00102).', required=True)
    required.add_argument('--slot', type=str, help='Module name (eg. 0,1,2).', required=True)
    required.add_argument('--board', type=str, help='Board name (eg. fc7ot2).', required=True)
    required.add_argument('--strip', type=str, default='0,1,2,3,4,5,6,7', help='strip number (eg. 0,1,2 default=all).', required=False)
    required.add_argument('--pixel', type=str, default='8,9,10,11,12,13,14,15', help='pixel number (eg. 8,9,15 default=all).', required=False)
    required.add_argument('--hybrid', type=str, default='0,1', help='hybrid number (default=0,1).', required=False)
    required.add_argument('--lpGBT', type=str, default='lpGBT_v1_PS.txt', help='lpGBT file (default=lpGBT_v1_PS.txt).', required=False)
    
    parser.add_argument('--useExistingModuleTest', type=str, nargs='?', const='', help='Read results from an existing module test. Skip ot_module_test run (for testing).')
    parser.add_argument('--useExistingXmlFile', type=str, nargs='?', const='', help='Specify an existing xml file without generating a new one (for testing). ')
#    parser.add_argument('--verbose', type=int, nargs='?', const=10000, default=-1, help='Verbose settings.')
    parser.add_argument('--edgeSelect', type=str, default='None', help='Select edgeSelect parameter (Default taken from PS_Module_template.xml).')
    parser.add_argument('--readOnlyID', type=bool, default=False, nargs='?', const=True, help='Skip test and read module ID.')
    parser.add_argument('--localPh2ACF', type=bool, default=False, nargs='?', const=True, help='Use local Ph2ACF instead of Docker.')
    parser.add_argument('--addNewModule', type=bool, default=False, nargs='?', const=True, help='Add new module to the database without asking y/n.')
    parser.add_argument('--g10', type=bool, nargs='?', const=True, help='Install 10g firmware (%s) instad of 5g (%s).'%(firmware_10G, firmware_5G))
    parser.add_argument('--runFpgaConfig', type=bool, nargs='?', const=True, help='Force run runFpgaConfig.')
    parser.add_argument('--skipUploadResults', type=bool, nargs='?', const=True, default=False, help='Skip running updateTestResults at the end of the test.')
    parser.add_argument('--skipMongo', type=bool, nargs='?', const=True, help='Skip upload to mondoDB (for testing).')
    parser.add_argument('--skipModuleCheck', type=bool, default=True, nargs='?', const=True, help='Do not throw exception if the module declared does not correspond to the module in the slot.')
    parser.add_argument('--firmware', type=str, nargs='?', const='', default="", help='Firmware used in fpgaconfig. Default=ps_twomod_oct23.bin')
    parser.add_argument('--xmlPyConfigFile', type=str, nargs='?', const="PS_Module_settings.py", default="PS_Module_settings.py", help='location of PS_Module_settings.py file with the XML configuration.')
    parser.add_argument('--ignoreConnection', type=bool, default=False, nargs='?', const=True, help='Ignore database connection check, ie. do not throw exception if there is a mismatch between the database connection and the module declared')

    
    print("Example: python3 moduleTest.py --module PS_26_05-IBA_00102 --slot 0 --board fc7ot2 --readOnlyID  --session session1")
    args = parser.parse_args()
    if args.localPh2ACF:
        print()
        print("I will use local Ph2ACF instead of Docker!")
        if "PH2ACF_BASE_DIR" in os.environ: 
            ph2acf = os.environ['PH2ACF_BASE_DIR']
        else:
            raise Exception("No Ph2ACF available (eg. no runCalibration). Please do 'source setup.sh' from Ph2ACF folder!")
        settingFolder = "%s/settings"%ph2acf
        from shellCommands import updateSettingsLink
        updateSettingsLink(settingFolder)
        print("Local Ph2ACF folder: %s"%ph2acf)
        print()
    localPh2ACF = args.localPh2ACF
    board = args.board
    lpGBTfile = args.lpGBT
    slots = args.slot.split(",")
    modules = args.module.split(",")
    if len(slots)!=len(modules):
        raise Exception("--slots and --modules must have the same number of objects. Check %s and %s."%(slots,modules))
    session = args.session
    edgeSelect = args.edgeSelect
    hybrids = [int(h) for h in args.hybrid.split(",") if h != ""]
    pixels = [int(h) for h in args.pixel.split(",") if h != ""]
    strips = [int(h) for h in args.strip.split(",") if h != ""]
    if len(strips)>0 and max(strips)>7 or min(strips)<0: raise Exception("strip numbers are allowed in [0,7] range. Strips: %s"%(str(strips)))
    if len(pixels)>0 and (max(pixels)>15 or min(strips)<0): raise Exception("strip numbers are allowed in [8,15] range. Pixels: %s"%(str(pixels)))
    
    
    ## check if the expected modules match the modules declared in the database for the slots
    from databaseTools import getModuleConnectedToFC7
    for i, slot in enumerate(slots):
        error = None
        moduleFromDB = getModuleConnectedToFC7(board.upper(), "OG%s"%slot)
        moduleFromCLI = modules[i]
        print("board %s, slot %s, moduleFromDB %s, moduleFromCLI %s"%(board, slot, moduleFromDB, moduleFromCLI))
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
                error = "Module %s is already in the connection database and it is expected in board %s and slot %s, not in board %s and slot %s."%(moduleFromCLI, fc7, og, board.upper(), "OG%s"%slot)
                print(error)
        else:
            if moduleFromDB != moduleFromCLI:
                error = "Module %s declared in the database for board %s and slot %s does not match the module declared in the command line (%s)."%(moduleFromDB, board, slot, modules[i])
                print(error)
            else:
                print("Module %s declared in the database for board %s and slot %s matches the module declared in the command line (%s)."%(moduleFromDB, board, slot, modules[i]))
        if error and not args.readOnlyID and args.ignoreConnection:
            raise Exception(error)
    readOnlyID = args.readOnlyID
    if readOnlyID: ##enable minimal configuration to get the hardware ID of the module
        hybrids = [hybrids[0]]
        pixels = []
        strips = [0]
    
    if args.firmware and args.g10:
        raise Exception("You cannot use --firmware and --10g option at the same time.")
    elif args.firmware:
        firmware = args.firmware
    elif args.g10:
        firmware = firmware_10G
    else:
        firmware = firmware_5G
    
    ## This will be replaced by a function that check which optical group are conntected to a specific slot
    opticalGroups = [int(s) for s in slots]

#    print("firmware",firmware)
#    verbose = args.verbose
    
    from pprint import pprint
    from tools import getROOTfile, getIDsFromROOT, getNoisePerChip, getResultsPerModule
    from shellCommands import fpgaconfig, runModuleTest, burnIn_readSensors 
    from makeXml import makeXml, makeNoiseMap, readXmlConfig, makeXmlPyConfig
    from databaseTools import uploadTestToDB, uploadRunToDB, getTestFromDB, addTestToModuleDB, getModuleFromDB, makeModuleNameMapFromDB, getRunFromDB, addNewModule
    
    ### read xml config file and create XML
    import shutil
    if args.useExistingModuleTest:
        matches = [folder for folder in os.listdir("Results") if args.useExistingModuleTest in folder ]
        if len(matches) != 1: raise Exception("%d matches of %s in ./Results/. %s"%( len(matches), args.useExistingModuleTest, str(matches)))
        folder = matches[0]
        xmlFilePath = "%s/%s"%("Results/"+folder, xmlPyConfigFile)
        if os.path.exists("%s/%s"%(xmlFilePath, xmlPyConfigFile)):
            xmlConfig = readXmlConfig(xmlPyConfigFile, folder=xmlFilePath)
        else:
            from makeXml import makeConfigFromROOTfile
            print("%s not found. Creating it from ROOT file."%xmlFilePath)
            xmlConfig = makeConfigFromROOTfile("Results/"+folder+"/Results.root")
        file = open(xmlFilePath, 'w')
        file.write("config =" + str(xmlConfig))
        file.close
#        xmlPyConfigFile = "Results/%s/PS_Module_settings.py"%folder
        xmlFile = "Results/%s/ModuleTest_settings.xml"%folder
    else:
        xmlPyConfigFile = args.xmlPyConfigFile
#        xmlConfig = readXmlConfig(xmlPyConfigFile)
        outFile="PS_Module_settings_autogenerated.py"
        xmlConfig = makeXmlPyConfig(board, opticalGroups, hybrids, strips, pixels, lpGBTfile, edgeSelect, outFile, Nevents=50)
        xmlPyConfigFile = outFile
        xmlFile = makeXml(xmlOutput, xmlConfig, xmlTemplate)
    
    pprint(xmlConfig)
    
    ### launch fpga_config
    if args.runFpgaConfig: fpgaconfig(xmlFile, firmware, localPh2ACF)
    
    ### launch ot_module_test (if useExistingModuleTest is defined, read the existing test instead of launching a new one)
    print("args.useExistingModuleTest",args.useExistingModuleTest)
    out = runModuleTest(xmlFile, args.useExistingModuleTest, localPh2ACF, minimal=readOnlyID) # 
    if out == "Run fpgaconfig":
        print("\n\nWARNING: You forgot to run fpgaconfig. I'm launching it now.\n")
        fpgaconfig(xmlFile, firmware, localPh2ACF)
        out = runModuleTest(xmlFile, args.useExistingModuleTest, localPh2ACF, minimal=readOnlyID) # 
    testID, date = out
    
    ### read the output file (if args.useExistingModuleTest is defined, read the that ROOT file)
    rootFile = getROOTfile(testID) if not args.useExistingModuleTest else getROOTfile(args.useExistingModuleTest) 
    
    ### get the lpGBT hardware ID for each module from the ROOT file (CHIPID registers, CHIPID0)
    # Note: each module is identified by (board_id, opticalGroup_id)
    # IDs is a map: IDs[(board_id, opticalGroup_id)] --> hardware ID
    IDs = getIDsFromROOT(rootFile, xmlConfig)
    
## To change hardware ID for testing ##
#    for bo in IDs:
#        IDs[bo] = IDs[bo]+1
    if args.useExistingXmlFile: ## remove missing IDs if running useExistingXmlFile (xmlConfigFil is fake)
        for x in list(IDs.keys()):
            if IDs[x] == "-1":
                print("Deleting ", x)
                del IDs[x]
                del xmlConfig["boards"][str(x[0])]["opticalGroups"][str(x[1])]
    if verbose>5: pprint(IDs)
    
    if readOnlyID and args.skipMongo:
        pprint (IDs)
        print()
        print("readOnlyID finished successfully.")
        print()
        exit(0) ##if you just want the hardware ID, stop here.
    
    ### Read noise "NoiseDistribution_Chip" for each chip
    # noisePerChip is a map "D_B(%s)_O(%s)_H(%s)_NoiseDistribution_Chip(%s)" --> noise
    noisePerChip = getNoisePerChip(rootFile , xmlConfig)
    if verbose>5: pprint(noisePerChip)
    
    ### Define an outcome result "pass" or "failed"
    result = getResultsPerModule(noisePerChip, xmlConfig)
    
    if not args.skipMongo: 
        ### create a map between lpGBT hardware ID to ModuleName and to MongoID, reading the module database
        hwToModuleName, hwToMongoID = makeModuleNameMapFromDB()
        
#            for b, o in board_opticals:
        board = 0 
        print()
        print("#####  Module check #####")
        error = False
        allModules = hwToModuleName.values()
        for i, opticalGroup in enumerate(opticalGroups):
            moduleExpected = modules[i] ## module passed from command line
            id_ = IDs[(board, opticalGroup)] if (board, opticalGroup) in IDs else -2 ## hardware IDs found in the test
            if int(id_)==-1 or int(id_)==-2:
                try:
                    message = "+++ Board %s Optical %d Module %d (NO MODULE FOUND). Expected %s. +++"%(xmlConfig["boards"][str(board)]["ip"], opticalGroup, int(id_), moduleExpected)
                except:
                    message = "+++ Board %s Optical %d Module %d (NO MODULE FOUND). Expected %s. +++"%(xmlConfig["boards"][board]["ip"], opticalGroup, int(id_), moduleExpected)
                print(message)
                if not args.skipModuleCheck: raise Exception(message)
                continue
            moduleFound = hwToModuleName[id_] if id_ in hwToModuleName else "unknown module" ## module found in the database matching the hardware ID
            try:
                print("+++ Board %s Optical %d Module %s (%d). Expected %s. +++"%(xmlConfig["boards"][board]["ip"], opticalGroup, moduleFound, int(id_), moduleExpected))
            except:
                print("+++ Board %s Optical %d Module %s (%d). Expected %s. +++"%(xmlConfig["boards"][str(board)]["ip"], opticalGroup, moduleFound, id_, moduleExpected))
            if moduleExpected in allModules: ## if the expected module is already in the database, check that the module found matches with the expected module
                if moduleFound!=moduleExpected:
                    print("DIFFERENT MODULE FOUND!!")
                    error = True
            else: ## if the expected module is not in the database, add it to the DB
                print("List of known modules:")
                for hwId in hwToModuleName:
                    print("%s (%d)"%(hwToModuleName[hwId], int(hwId)))
                print("Module %s is not yet in the database."%(moduleExpected))
                print("HwId %d found."%(int(id_)))
                if id_ in hwToModuleName and int(id_)!=-1:
                    message = "HwId %d is already associated to module %s.\nPlease fix the module name used."%(id_, hwToModuleName[id_])
                    print(message)
                    if not args.skipModuleCheck: raise Exception(message)
                if int(id_)!=-1 and not args.skipModuleCheck:
                    if args.addNewModule:
                        answer = "y" ## add the module without asking
                    else:
                        answer = input("Do you want to add module with hwID %d as %s in the database? (y/n): "%(id_, moduleExpected))
                    if answer == "y" or answer == "yes" or answer == "Y":
                        addNewModule(moduleExpected, id_) ## the DB function will check if the hardware ID is already used by another module
                    else:
                        raise Exception("I cannot work with unknown modules.")

        if error:
            message = "The modules declared in --modules (%s) do not correspond to the module found in --slots (%s) of --board (%s). See above for more details."%(str(modules), str(opticalGroups),str(board))
            print(message)
            if not args.skipModuleCheck: raise Exception(message) 
        if readOnlyID:
            print()
            print("readOnlyID finished successfully.")
            print()
            exit(0) ##if you just want the hardware module names, stop here.
        
        ### convert IDs of modules used in the test to ModuleID and to MongoID ()
        board_opticals = list(IDs.keys())
        moduleNames = [ hwToModuleName[IDs[bo]] for bo in board_opticals ]
        moduleMongoIDs = [ hwToMongoID[IDs[bo]] for bo in board_opticals ]
        
        ## upload all files
        for file in [xmlPyConfigFile, xmlOutput, rootFile.GetName(), "logs/%s.log"%testID]: #copy output files to CernBox
            newFile = webdav_wrapper.write_file(file, "/%s/%s"%(testID, file))
            if verbose>1: print("Uploaded %s"%newFile)
        
        ## copy some important files (xml, log, py) in .../Results folder
        resultFolder = rootFile.GetName()[:rootFile.GetName().rfind("/")]
        for file in [xmlPyConfigFile, xmlOutput, "logs/%s.log"%testID]: #copy output files to CernBox
            if args.useExistingModuleTest and (file == xmlPyConfigFile or file == xmlOutput): continue
            if file != rootFile.GetName():
                shutil.copy(file, resultFolder)
        
        ## make a zip file and upload it
        zipFile = "output"
        if verbose>20: print("shutil.make_archive(zipFile, 'zip', resultFolder)", zipFile, resultFolder)
        shutil.make_archive(zipFile, 'zip', resultFolder)
        if verbose>20: print("Done")
        newFile = webdav_wrapper.write_file(zipFile+".zip", "/%s/output.zip"%(testID))
        if verbose>0: print("Uploaded %s"%newFile)
        
        boardMap, moduleMap, noiseMap = makeNoiseMap(xmlConfig, noisePerChip, IDs, hwToModuleName)
        fakeRunResults = dict()
        for hwId in noiseMap:
            fakeRunResults[hwId] = "boh"
        date = date.replace(" ","T").split(".")[0] # drop ms
        if args.useExistingModuleTest:
            date = str(rootFile.Get("Detector/CalibrationStartTimestamp_Detector")).replace(" ","T")
        newRun = {
            'runDate': date, 
            'runSession': session,
            'runStatus': 'done',
            'runType': 'Type1',
            'runBoards': boardMap, 
#            E.g.
#            {
#                3: 'fc7ot2',
#                4: 'fc7ot3',
#            },
            'runModules' : moduleMap,
#            E.g.
#            { ## (board, optical group) : (moduleID, hwIDmodule)
#                'fc7ot2_optical0' : ("M123", 67),
#                'fc7ot2_optical1' : ("M124", 68),
#                'fc7ot3_optical2' : ("M125", 69),
#            },
            'runNoise' : noiseMap,
#            E.g.
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
#            },
#            'runResults' : fakeRunResults, ##E.g pass/failed
            'runConfiguration' : xmlConfig,
            'runFile' : "https://cernbox.cern.ch/files/link/public/%s/%s"%(hash_value_read,newFile)
        }
        
        print("Output uploaded to %s"%newFile)
        print("CERN box link (folder): https://cernbox.cern.ch/files/link/public/%s/%s"%(hash_value_read,testID))
        print("CERN box link (zip file): https://cernbox.cern.ch/files/link/public/%s/%s"%(hash_value_read,newFile))
        
        test_runName = uploadRunToDB(newRun)
        
        print("moduleTest.py completed.")
        print("test_runName: %s."%test_runName)
        run = getRunFromDB(test_runName)
        from updateTestResult import updateTestResult
        print()
        print("RUN:")
        print(run)
        print()
        print("SINGLE MODULE TEST:")
        for moduleTestName in run['moduleTestName']:
            print("######## Single Module Test: %s ########################" %moduleTestName)
            if not args.skipUploadResults and moduleTestName[0]!="-": ## skip analysis if skipUploadResults or test failed (moduleName = -1)
                print("Running updateTestResult")
                updateTestResult(moduleTestName)
                print("################################################")


