### Default values 
verbose = 100
sessionName = 'session1'
xmlConfigFile = "PS_Module_settings.py"
ip="192.168.0.45"
port=5005
xmlOutput="ModuleTest_settings.xml"
xmlTemplate="PS_Module_template.xml"
firmware="ps_twomod_oct23.bin" ##5 GBps
#firmware="ps8m10gcic2l12octa.bin" ##10 GBps
skipReadFNALsensors = True
runFpgaConfig = False ## it will run automatically if necessary
useExistingModuleTest = False
skipMongo = False
useExistingXmlFile = False
## command used to launch commands through Docker (podman)
podmanCommand = 'podman run  --rm -ti -v $PWD/Results:/home/cmsTkUser/Ph2_ACF/Results/ -v $PWD/logs:/home/cmsTkUser/Ph2_ACF/logs/ -v $PWD/..:$PWD/.. -v /etc/hosts:/etc/hosts -v ~/private/webdav.sct:/root/private/webdav.sct  -v /home/thermal/suvankar/power_supply/:/home/thermal/suvankar/power_supply/ --net host  --entrypoint sh  docker.io/sdonato/pisa_module_test:ph2_acf_v4-17 -c "%s"'
prefixCommand = 'source /home/cmsTkUser/Ph2_ACF/setup.sh && cd /home/thermal/Ph2_ACF_docker/BurnIn_moduleTest '

### Fake values used for testing
operator = "Mickey Mouse"
temps = [1.2, 4.5]
## assign these lpGBT hardware IDs to some random modules (they will be in the module database)
lpGBTids = ['3962125297', '42949672', '42949673', '42949674', '2762808384', '0x00', '0x67']

### Test (everything should be commented out during actual runs!)
#skipReadFNALsensors = True
#skipMongo = True
#useExistingModuleTest = "T2023_12_01_14_03_44_633194" ## read existing module test instead of launching a new test!
#useExistingModuleTest = "T2023_12_06_10_35_59_620446" ## read existing module test instead of launching a new test!
useExistingModuleTest = "M103_Run176" ## read existing module test instead of launching a new test!
#useExistingXmlFile = "PS_Module_v2p1.xml"
#useExistingXmlFile = "ModuleTest_settings.xml"
#useExistingXmlFile = "ot3.xml"
#podmanCommand = "%s" ##if your are running directly the software inside docker or with a standalone code

### webdav keys
hash_value_location = "~/private/webdav.sct" #echo "xxxxxxxxxxxxxxx|xxxxxxxxxxxxxxx" > ~/private/webdav.sct
webdav_url = "https://cernbox.cern.ch/remote.php/dav/public-files"
from webdavclient import WebDAVWrapper
import os
hash_value_read, hash_value_write = open(os.path.expanduser(hash_value_location)).read()[:-1].split("\n")[0].split("|")
webdav_wrapper = WebDAVWrapper(webdav_url, hash_value_read, hash_value_write)
#run = "RunXXX"
#dname = "/%s"%run
#webdav_wrapper.mkDir(dname)
#file = "ModuleTest_settings.xml"
#newFile = webdav_wrapper.write_file(file, "/%s/%s"%(run, file))
#print(dir, newFile)


if __name__ == '__main__':
    from pprint import pprint
    from tools import getROOTfile, getIDsFromROOT, getNoisePerChip, getResultsPerModule
    from shellCommands import fpgaconfig, runModuleTest, burnIn_readSensors
    from makeXml import makeXml, makeNoiseMap, readXmlConfig
    from databaseTools import uploadTestToDB, uploadRunToDB, getTestFromDB, addTestToModuleDB, getModuleFromDB, makeModuleNameMapFromDB
    
    ### read xml config file and create XML
    if useExistingXmlFile:
        xmlFile = useExistingXmlFile
        xmlConfig = {"boards" : {} }
    else:
        xmlConfig = readXmlConfig(xmlConfigFile)
        xmlFile = makeXml(xmlOutput, xmlConfig, xmlTemplate)
    
    ### launch fpga_config
    if runFpgaConfig: fpgaconfig(xmlFile, firmware)
    
    ### launch ot_module_test (if useExistingModuleTest is defined, read the existing test instead of launching a new one)
    out = runModuleTest(xmlFile, useExistingModuleTest) # 
    if out == "Run fpgaconfig":
        print("\n\nWARNING: You forgot to run fpgaconfig. I'm launching it now.\n")
        fpgaconfig(xmlFile, firmware)
        out = runModuleTest(xmlFile, useExistingModuleTest) # 
    testID, date = out
    
    ### read the output file (if useExistingModuleTest is defined, read the that ROOT file)
    rootFile = getROOTfile(testID) if not useExistingModuleTest else getROOTfile(useExistingModuleTest) 
    
    ### Read noise "NoiseDistribution_Chip" for each chip
    # noisePerChip is a map "D_B(%s)_O(%s)_H(%s)_NoiseDistribution_Chip(%s)" --> noise
    noisePerChip = getNoisePerChip(rootFile , xmlConfig)
    if verbose>5: pprint(noisePerChip)
    
    ### Define an outcome result "pass" or "failed"
    result = getResultsPerModule(noisePerChip, xmlConfig)
    
    ### get the lpGBT hardware ID for each module from the ROOT file (CHIPID registers, CHIPID0)
    # Note: each module is identified by (board_id, opticalGroup_id)
    # IDs is a map: IDs[(board_id, opticalGroup_id)] --> hardware ID
    IDs = getIDsFromROOT(rootFile, xmlConfig)
    if verbose>5: pprint(IDs)
    
    if not skipMongo: 
        ### create a map between lpGBT hardware ID to ModuleName and to MongoID, reading the module database
        hwToModuleName, hwToMongoID = makeModuleNameMapFromDB()
        
        ### convert IDs of modules used in the test to ModuleID and to MongoID ()
        board_opticals = list(IDs.keys())
        moduleNames = [ hwToModuleName[IDs[bo]] for bo in board_opticals ]
        moduleMongoIDs = [ hwToMongoID[IDs[bo]] for bo in board_opticals ]
        
        ### Read sensors from FNAL box
        if not skipReadFNALsensors: temps = burnIn_readSensors()
        
        import shutil
        ## upload all files
        for file in [xmlConfigFile, xmlOutput, rootFile.GetName(), "logs/%s.log"%testID]: #copy output files to CernBox
            newFile = webdav_wrapper.write_file(file, "/%s/%s"%(testID, file))
            if verbose>1: print("Uploaded %s"%newFile)
        
        ## copy some important files (xml, log, py) in .../Results folder
        resultFolder = rootFile.GetName()[:rootFile.GetName().rfind("/")]
        for file in [xmlConfigFile, xmlOutput, "logs/%s.log"%testID]: #copy output files to CernBox
            if file != rootFile.GetName():
                shutil.copy(file, resultFolder)
        
        ## make a zip file and upload it
        zipFile = "output"
        if verbose>20: print("shutil.make_archive(zipFile, 'zip', resultFolder)", zipFile, resultFolder)
        shutil.make_archive(zipFile, 'zip', resultFolder)
        if verbose>20: print("Done")
        newFile = webdav_wrapper.write_file(zipFile+".zip", "/%s/output.zip"%(testID))
        if verbose>0: print("Uploaded %s"%newFile)
        
        ### Create test result and upload it to "test" DB
        # see https://github.com/pisaoutertracker/testmongo/blob/f7e032c3dafa7954f834810903ea8ac9dc5bdbd0/populate_db.py#L70C6-L70C8
#        testResult = {
#                "testID": testID,
#                "modules_list": moduleMongoIDs,
#                "testType": "Type1",
#                "testDate": date,
#                "testOperator": operator,
#                "testStatus": "completed",
#                "testResults": {
#                    "result": result,
#                    "noisePerChip": noisePerChip,
#                    "boards": makeBoardMap(xmlConfig),
#                    "temperatures": temps,
#                    "xmlConfig": xmlConfig
#                },
#                "outputFile": newFile,
#                "runFolder" : testID
#        #        ## Not manadatory
#        }
        
        boardMap, moduleMap, noiseMap = makeNoiseMap(xmlConfig, noisePerChip, IDs, hwToModuleName)
        fakeRunResults = dict()
        for hwId in noiseMap:
            fakeRunResults[hwId] = "boh"
        newRun = {
#            'runDate': date,
#            'runDate': date.split(" ")[0],
            'runDate': date.replace(" ","T").split(".")[0], # drop ms
#            'test_runID': testID,
#            'runOperator': 'Kristin Jackson',
            'runSession': sessionName,
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
        
#        pprint(newRun)
        
#        uploadTestToDB(
#            testID = testID,
#            testResult = testResult,
#        )
        
        print("Output uploaded to %s"%newFile)
        print("CERN box link (folder): https://cernbox.cern.ch/files/link/public/%s/%s"%(hash_value_read,testID))
        print("CERN box link (zip file): https://cernbox.cern.ch/files/link/public/%s/%s"%(hash_value_read,newFile))
        
        uploadRunToDB(newRun)
        
#        ### Read from test DB the test just uploaded and print it
#        test = getTestFromDB(testID = testID)
#        if verbose>2: 
#            print("\n #####     Check Test %s on MongoDB    ##### \n"%testID)
#            pprint(test)
        
        ### Append the test result to the "tests" list in the module DB, per each module
#        for moduleID in moduleIDs:
#            if moduleID == "-1": 
#                print("\n WARNING: Skipping missing (crashing) module.")
#                continue
#            module = getModuleFromDB(moduleID = moduleID)
#            if 'message' in module and module['message']=="Module not found":
#                print("\n WARNING: Module %s not found. Please check: \ncurl -X GET -H 'Content-Type: application/json' 'http://192.168.0.45:5000/modules/%s'"%(moduleID, moduleID))
#                print("Skipping module %s"%moduleID)
#                continue
#                
            
#            ### Print the module from DB BEFORE the update
#            if verbose>2: 
#                print("\n #####     Check Module %s on MongoDB - before    ##### \n"%moduleID)
#                pprint(module)
            
#            ### Add test to the modules database
#            # throw an exception if the test is already existing
#            if not test["_id"] in module["tests"]:
#                updatedTestList = module["tests"]
#                updatedTestList.append(test["_id"])
#                addTestToModuleDB( 
#                    moduleID = moduleID, 
#                    updatedTestList = updatedTestList
#                )
#            ### Print the module from DB AFTER the update
#                if verbose>2: 
#                    print("\n #####     Check Module %s on MongoDB - after     ##### \n"%moduleID)
#                    pprint(getModuleFromDB(moduleID = moduleID))
#            else:
#                raise Exception("Test %s (%s) is already included in %s (%s) test list %s."%(test["testID"], test["_id"], module["moduleID"], module["_id"], module["tests"]))
#        

