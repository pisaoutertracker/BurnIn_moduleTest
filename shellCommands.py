import os
import subprocess
from moduleTest import verbose, podmanCommand, prefixCommand, lastPh2ACFversion

#verbose = 1000
### Launch a command from shell

def runCommand(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, executable='/bin/bash', showInPrompt=True):
    if showInPrompt: 
        command = command + " 2>&1 | tee /dev/tty"
    print("Launching command: %s"%command)
    try:
        return subprocess.run(command, check=check, stdout=stdout, stderr=stderr, shell=shell, timeout=7200)
    except subprocess.CalledProcessError as e:
        print(e.output)
        print(type(e), type(e.output))
        raise Exception("{}".format(e.output.decode('utf-8')))

### Burn-in commands

def updateSettingsLink(settingFolder):
    if verbose>0: print("Calling updateSettingsLink()")
    print(updateSettingsLink)
    output = runCommand("rm settings ; ln -s %s ."%settingFolder)
    if verbose>1: print(output)

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
    temps = output.stdout.decode().split("buffer: [")[1].split("]")[0]
    temps = [float(temp) for temp in temps.split(",")]
    if verbose>1: print(output)
    return temps

def burnIn_setTemperature(temperature):
    if verbose>0: print("Calling burnIn_setTemperature(%f)"%temperature)
    output = runCommand("/home/thermal/suvankar/power_supply//setTemperatureJulabo.sh .3%f"%temperature)
    if verbose>1: print(output)

### Copy settings/PS_Module_v2p1.xml locally (note: settings is in Docker, unless --localPh2ACF is used)

def getGitTagFromHash(gitHash):
    # git describe --tags --exact-match 804c5ba815fb334f6e2756dbb96215835bc5006b
    if verbose>0: print("Calling getGitTagFromHash()")
    listOfTags = runCommand("git ls-remote --tags ssh://git@gitlab.cern.ch:7999/cms_tk_ph2/Ph2_ACF.git" , showInPrompt=False if verbose<10 else True).stdout.decode().strip().split("\n")
    for tag in listOfTags:
        commit, tag = tag.split("\t")
        if commit == gitHash[:len(commit)]:
            if verbose>10: print("Git hash %s corresponds to tag %s"%(gitHash, tag))
            return tag.replace("refs/tags/","").replace("^{}","")
    print()
    print("ERROR [getGitTagFromHash]: Git hash %s not found in gitlab.cern.ch/cms_tk_ph2/Ph2_ACF.git"%gitHash)
    print("Available tags are:")
    for tag in listOfTags:
        print(tag)
    print("The git commit hash will be used instead of the tag.")
    print()
    return gitHash

def copyXml(ph2ACFversion=lastPh2ACFversion):
    if verbose>0: print("Calling copyXml()")
    if ph2ACFversion=="local":
        print("Copying settings/PS_Module_v2p1.xml locally.")
        command = "cp settings/PS_Module_v2p1.xml ."
        output = runCommand(command)
    else:
        print("Copying settings/PS_Module_v2p1.xml (from Docker) locally.")
        command = "%s && cp settings/PS_Module_v2p1.xml ."%(prefixCommand)
        print(podmanCommand)
        output = runCommand(podmanCommand%(ph2ACFversion,command))
    error = output.stderr.decode()
    if error:
        print()
        print("|"+error+"|")
        raise Exception("Generic Error running copyXml. Check the error above. Command: %s"%output.args)
    if verbose>1: print(output)

### Launch FPGA config (to be used after FC7 reset)

# def fpgaconfig(xmlFile, firmware, ph2ACFversion=lastPh2ACFversion):
#     if verbose>0: print("Calling fpgaconfig()", xmlFile, firmware)
#     if ph2ACFversion=="local":
#         command = "fpgaconfig -c %s -i %s"%(xmlFile, firmware)
#         output = runCommand(command)
#     else:
#         ## 
#         command = "%s && fpgaconfig -c %s -i %s"%(prefixCommand + "&& cd $PH2ACF_BASE_DIR", xmlFile, firmware)
#         output = runCommand(podmanCommand%(ph2ACFversion,command))
#     error = output.stderr.decode()
#     if error:
#         print()
#         print("|"+error+"|")
#         raise Exception("Generic Error running fpgaconfig. Check the error above. Command: %s"%output.args)
#     if verbose>1: print(output)

def fpgaconfigNew(options, ph2ACFversion=lastPh2ACFversion):
    if verbose>0: print("Calling fpgaconfigNew()", options)
    if ph2ACFversion=="local":
        command = "fpgaconfig %s "%(options)
        output = runCommand(command)
    else:

        ## Drop all -v options of Docker except the one used to link /etc/hosts
        podmanCommandMinimal = ""
        for word in podmanCommand.split("-"):
            ## Remove all volume bindings except for /etc/hosts
            if word.startswith("v"):
                if "/etc/hosts" in word:
                    podmanCommandMinimal += "-"+word
                    ## Add also the binding for the xml file directly to the Ph2_ACF folder
                    podmanCommandMinimal += " -v $PWD/ModuleTest_settings_for_fpgaconfigPisa.xml:/home/cmsTkUser/Ph2_ACF/ModuleTest_settings_for_fpgaconfigPisa.xml:z "
                else:
                    continue
            else:
                podmanCommandMinimal += "-"+word

        podmanCommandMinimal = podmanCommandMinimal[1:] # remove initial -
        import os
        command = "%s && fpgaconfig %s"%(prefixCommand.replace(os.getcwd(), "/home/cmsTkUser/Ph2_ACF/"), options)
        output = runCommand(podmanCommandMinimal%(ph2ACFversion,command))
    error = output.stderr.decode()
    if error:
        print()
        print("|"+error+"|")
        raise Exception("Generic Error running fpgaconfig. Check the error above. Command: %s"%output.args)
    if verbose>1: print(output)
    return output

### Call fpgaconfigPisa (to be used after FC7 reset)
def fpgaconfigPisa(board, firmware):
    if verbose>0: print("Calling fpgaconfigPisa()", board, firmware)
    command = f"fpgaconfigPisa {board} -i {firmware}"

    ## Run command locally
    output = runCommand(command)
    error = output.stderr.decode()

    if error:
        print()
        print("|"+error+"|")
        raise Exception("Generic Error running fpgaconfigPisa. Check the error above. Command: %s"%output.args)
    if verbose>1: print(output)
    success = False
    for l in output.stdout.decode().split("\n"):
        if "fpgaconfigPisa]Firmware" in l and "successfully uploaded to board" in l:
            success = True
            break
    if not success:
        print()
        print("|"+output.stdout.decode()+"|")
        raise Exception("fpgaconfigPisa did not complete successfully. Check the output above. Command: %s"%output.args)
    return output

### Make testID from current date and time

from datetime import datetime
def getDateTimeAndTestID():
    date = str(datetime.now())
    testID = "T"+date.replace("-","_").replace(":","_").replace(" ","_").replace(".","_")
    return date, testID

### Launch ot_module_test, given an xml file.
# if useExistingModuleTest, skip the test and read the existing log file

def runModuleTest(xmlFile="PS_Module.xml", useExistingModuleTest=False, ph2ACFversion=lastPh2ACFversion, commandOption="readOnlyID", logFolder="logs"):
    global error 
    if verbose>0: print("Calling runModuleTest()", xmlFile, useExistingModuleTest, ph2ACFversion, logFolder, commandOption)
    date, tmp_testID = getDateTimeAndTestID()
    logFile = "%s/%s.log"%(logFolder,tmp_testID)
    if verbose>0: print(tmp_testID,logFile)
    if not useExistingModuleTest: # -w $PWD 
        if commandOption=="readOnlyID":
            commandOption = "configureonly"
        if ph2ACFversion=="local":
            command = "runCalibration -b -f %s -c %s  2>&1 | tee %s"%(xmlFile, commandOption, logFile)
            if commandOption=="help": command = "runCalibration --help"
            output = runCommand(command)
        else:
            command = "%s && runCalibration -b -f %s -c %s 2>&1 | tee %s"%(prefixCommand, xmlFile, commandOption, logFile)
            if commandOption=="help": command = "%s && runCalibration --help"%(prefixCommand)
            output = runCommand(podmanCommand%(ph2ACFversion,command))
#        command = "%s && ot_module_test -f %s -t -m -a --reconfigure -b --moduleId %s --readIDs | tee %s"%(prefixCommand, xmlFile,tmp_testID,logFile)
    else:
        log = "logs/%s.log"%useExistingModuleTest
        import os
        if os.path.exists(log):
            output = runCommand("cat %s 2>&1 | tee %s"%(log, logFile))
        else:
            ## fake log if missing
            print("######################################")
            print("######################################")
            print("WARNING: log file %s not found. Using a fake log file."%log)
            print("######################################")
            print("######################################")
            output = runCommand("echo 'Closing result file: Results/%s/Results.root' 2>&1 | tee %s"%(useExistingModuleTest, logFile))
    if verbose>10: print(output)
    error = output.stdout.decode() ## if you are not launching command through podman/Docker you should use "stderr" instead.
    ## Remove known warning
    error = error.replace("Warning in <EnableImplicitMT>: Cannot enable implicit multi-threading with 0 threads, please build ROOT with -Dimt=ON\n", "")
    ## Raise an exception, with an explanation, if something went wrong
    if "ControlHub returned error code 3" in error:
        print()
        print(error)
        raise Exception("ControlHub returned error code 3.  \n Please check that: 1) your FC7 is on, 2) FC7 is connected to the Ethernet (check LEDs in the router), 3) you are using the correct port (eg. 50001).  \n Command: %s"%output.args)

    if "what():  Error: calibration tag " in error and "does not exist" in error:
        print()
        print(error)
        raise Exception("The option -c option that you passed is not allowed.\n See 'what():  Error: calibration tag ...' line above for more info.\nUse -c help for more infos about the -c option allowed.\n Command: %s"%output.args)
    if "Host not found (authoritative)" in error:
        print()
        print(error)
        raise Exception("Host not found.  \n Please check that all hosts used (eg. fc7ot3) are defined in /etc/hosts.  \n Command: %s"%output.args)
    if "ExceptionHandler Error: No object enabled in fDetectorContainer" in error:
        print()
        print(error)
        if "lpGBT TX Ready\x1b[1m\x1b[31m\t : FAILED" in output.stdout.decode():
            print("ExceptionHandler Error: No object enabled in fDetectorContainer.  \n Please check that you have installed the firmware (fpgaconfig). Command: %s"%output.args)
            return "Run fpgaconfigPisa"
        else:
            raise Exception("ExceptionHandler Error: No object enabled in fDetectorContainer.  \n All modules seem off. Please check that the low voltages are turned on. Check that some light is coming out from the optical fibers that you selected.  \n It might be due to a wrong version of the firmware installed in the FC7. \n Command: %s"%output.args)
#    if "ExceptionHandler Error: No object enabled in fDetectorContainer" in error:
#        print()
#        print(error)
#        raise Exception("ExceptionHandler Error: No object enabled in fDetectorContainer. All modules seem off. Please check that the low voltages are turned on. Check that some light is coming out from the 
    if error and not "Closing result file:" in error:
        print()
        print("|"+error+"|")
        raise Exception("Generic Error running ot_module_test. Check the error above. Command: %s"%output.args)
    
    ## find ROOT file from log file:
    if "Closing result file: " in error:
        rootFile = error.split("Closing result file: ")[1].split(".root")[0]+".root" ##eg. Results/Run_28/Results.root
        testID = rootFile.split("/")[1] ## get "Run_28"
        import shutil
        #shutil.copytree("Results/"+testID, "Results/"+tmp_testID)
        shutil.copy(logFile, logFile.replace(tmp_testID,testID))
        print("Results copied to %s"%logFile.replace(tmp_testID,testID))
    else:
        testID = tmp_testID
    if useExistingModuleTest:
        testID = useExistingModuleTest
    return testID, date


### This code allow you to test this code using "python3 shellCommands.py"

if __name__ == '__main__':
#    verbose = -1
    print(getGitTagFromHash("804c5ba815fb334f6e2756dbb96215835bc5006b"))

    runCommand('podman run  --rm -ti -v $PWD/Results:/home/cmsTkUser/Ph2_ACF/Results/:z -v $PWD/logs:/home/cmsTkUser/Ph2_ACF/logs/:z -v $PWD:$PWD:z -v /etc/hosts:/etc/hosts -v ~/private/webdav.sct:/root/private/webdav.sct:z  --net host  --entrypoint bash  gitlab-registry.cern.ch/cms-pisa/pisatracker/pisa_module_test:ph2_acf_v6-00 -c "\cp  /usr/share/zoneinfo/Europe/Rome /etc/localtime && cd /home/cmsTkUser/Ph2_ACF && source setup.sh && cd /home/thermal/BurnIn_moduleTest && runCalibration --help"')
    
    xmlFile = "ModuleTest_settings.xml"
    firmware="ps_twomod_oct23.bin"
    useExistingModuleTest=False
    
    temps = burnIn_readSensors()
    print("\ntemps:")
    print(temps)
    
    date, testID = getDateTimeAndTestID()
    print("\ntestID-1:")
    print(date, testID)
    print()
    
#    fpgaconfig(xmlFile, firmware)
    board = "fc7ot3"
    print("\nCalling fpgaconfigPisa(%s, %s)"%(board, firmware))
    fpgaconfigPisa(board, firmware)
    print()

    print()
    testID, date = runModuleTest(xmlFile, useExistingModuleTest)
    print("\ntestID-2:")
    print(date, testID)
    

