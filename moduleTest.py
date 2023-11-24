### Default values 
verbose = 100
xmlConfigFile = "PS_Module_settings.py"
ip="192.168.0.45"
port=5000
xmlOutput="ModuleTest_settings.xml"
xmlTemplate="PS_Module_template.xml"
firmware="ps_twomod_oct23.bin"
skipReadFNALsensors = True
runFpgaConfig = False ## it will run automatically if necessary
useExistingModuleTest = False
skipMongo = False

### Fake values used for testing
operator = "Mickey Mouse"
temps = [1.2, 4.5]
## assign these lpGBT hardware IDs to some random modules (they will be in the module database)
lpGBTids = ['3962125297', '42949672', '42949673', '42949674', '0x00', '0x67']

### Test (everything should be commented out during actual runs!)
#skipReadFNALsensors = True
#skipMongo = True
#useExistingModuleTest = "test_m20gradi" ## read existing module test instead of launching a new test!

### webdav keys
hash_value_location = "~/private/webdav.sct" #echo "xxxxxxxxxxxxxxx|xxxxxxxxxxxxxxx" > ~/private/webdav.sct
webdav_url = "https://cernbox.cern.ch/remote.php/dav/public-files"
from webdavclient import WebDAVWrapper
import os
hash_value_read, hash_value_write = open(os.path.expanduser(hash_value_location)).read()[:-1].split("|")
webdav_wrapper = WebDAVWrapper(webdav_url, hash_value_read, hash_value_write)
#run = "RunXXX"
#dname = "/%s"%run
#webdav_wrapper.mkDir(dname)
#file = "ModuleTest_settings.xml"
#newFile = webdav_wrapper.write_file(file, "/%s/%s"%(run, file))
#print(dir, newFile)


if __name__ == '__main__':
    from pprint import pprint
    from tools import getROOTfile, getIDsFromROOT, getNoisePerChip, getResultPerModule
    from shellCommands import fpgaconfig, runModuleTest, burnIn_readSensors
    from makeXml import makeXml, makeBoardMap, readXmlConfig
    from databaseTools import uploadTestToDB, getTestFromDB, addTestToModuleDB, getModuleFromDB, makeModuleIdMapFromDB

    ### read xml config file and create XML
    xmlConfig = readXmlConfig(xmlConfigFile)
    xmlFile = makeXml(xmlOutput, xmlConfig, xmlTemplate)
    
    ### launch fpga_config
    if runFpgaConfig: fpgaconfig(xmlFile, firmware)
    
    ### launch ot_module_test (if useExistingModuleTest is defined, read the existing test instead of launching a new one)
    out = runModuleTest(xmlFile, useExistingModuleTest) # 
    if out == "Run fpgaconfig":
        print("\n\nWARNING: You forgot to run fpgaconfig. Launching it not.\n")
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
    result = getResultPerModule(noisePerChip, xmlConfig)
    
    ### get the lpGBT hardware ID for each module from the ROOT file (CHIPID registers, CHIPID0)
    # Note: each module is identified by (board_id, opticalGroup_id)
    # IDs is a map: IDs[(board_id, opticalGroup_id)] --> hardware ID
    IDs = getIDsFromROOT(rootFile, xmlConfig)
    if verbose>5: pprint(IDs)
    
    if not skipMongo: 
        ### create a map between lpGBT hardware ID to ModuleID and to MongoID, reading the module database
        hwToModuleID, hwToMongoID = makeModuleIdMapFromDB()
        
        ### convert IDs of modules used in the test to ModuleID and to MongoID ()
        board_opticals = list(IDs.keys())
        moduleIDs = [ hwToModuleID[IDs[bo]] for bo in board_opticals ]
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
        testResult = {
                "testID": testID,
                "modules_list": moduleMongoIDs,
                "testType": "Type1",
                "testDate": date,
                "testOperator": operator,
                "testStatus": "completed",
                "testResults": {
                    "result": result,
                    "noisePerChip": noisePerChip,
                    "boards": makeBoardMap(xmlConfig),
                    "temperatures": temps,
                    "xmlConfig": xmlConfig
                },
                "outputFile": newFile,
                "runFolder" : testID
        #        ## Not manadatory
        }

        uploadTestToDB(
            testID = testID,
            testResult = testResult,
        )

        ### Read from test DB the test just uploaded and print it
        test = getTestFromDB(testID = testID)
        if verbose>2: 
            print("\n #####     Check Test %s on MongoDB    ##### \n"%testID)
            pprint(test)

        ### Append the test result to the "tests" list in the module DB, per each module
        for moduleID in moduleIDs:
            if moduleID == "-1": 
                print("\n WARNING: Skipping missing (crashing) module.")
                continue
            module = getModuleFromDB(moduleID = moduleID)
            if 'message' in module and module['message']=="Module not found":
                print("\n WARNING: Module %s not found. Please check: \ncurl -X GET -H 'Content-Type: application/json' 'http://192.168.0.45:5000/modules/%s'"%(moduleID, moduleID))
                print("Skipping module %s"%moduleID)
                continue
                

            ### Print the module from DB BEFORE the update
            if verbose>2: 
                print("\n #####     Check Module %s on MongoDB - before    ##### \n"%moduleID)
                pprint(module)

            ### Add test to the modules database
            # throw an exception if the test is already existing
            if not test["_id"] in module["tests"]:
                updatedTestList = module["tests"]
                updatedTestList.append(test["_id"])
                addTestToModuleDB( 
                    moduleID = moduleID, 
                    updatedTestList = updatedTestList
                )
            ### Print the module from DB AFTER the update
                if verbose>2: 
                    print("\n #####     Check Module %s on MongoDB - after     ##### \n"%moduleID)
                    pprint(getModuleFromDB(moduleID = moduleID))
            else:
                raise Exception("Test %s (%s) is already included in %s (%s) test list %s."%(test["testID"], test["_id"], module["moduleID"], module["_id"], module["tests"]))
        
        print("Output uploaded to %s"%newFile)
        print("CERN box link (folder): https://cernbox.cern.ch/files/link/public/zcvWnJKEk7YgSBh/%s"%testID)
        print("CERN box link (zip file): https://cernbox.cern.ch/files/link/public/zcvWnJKEk7YgSBh/%s"%newFile)

