# BurnIn_moduleTest
`BurnIn_moduleTest` code runs PS module test using [Ph2_ACF](https://gitlab.cern.ch/cms_tk_ph2/Ph2_ACF) (`runCalibration -b -c calibrationandpedenoise -f ModuleTest_settings.xml`), reads the output, and uploads the result on MongoDB and CERN box.
The final result is uploaded on webpages like [Module_PS_26_05-IBA_00102_Run_run386_Result_Test7](https://cmstkita.web.cern.ch/Pisa/TBPS/navigator.php/Uploads//test3/Module_PS_26_05-IBA_00102_Run_run386_Result_Test7/results_qdjwe.zip/) and on the [TBPS database](https://cmstkita.web.cern.ch/Pisa/TBPS/).

## Installation

```
git clone https://github.com/pisaoutertracker/BurnIn_moduleTest.git
cd BurnIn_moduleTest
```

The code assumes that `/etc/hosts` contains the definition of the fc7ot IP (eg. `192.168.0.191 fc7ot3`) 
and also some private files containing passwords:
- `~/private/influx.sct` (used [here](https://github.com/pisaoutertracker/BurnIn_moduleTest/blob/ph2_acf_v5-03/updateTestResult.py#L517-L563))
- `~/private/webdav.sct` (used [here](https://github.com/pisaoutertracker/BurnIn_moduleTest/blob/ph2_acf_v5-03/updateTestResult.py#L626C5-L630) and [here](https://github.com/pisaoutertracker/BurnIn_moduleTest/blob/ph2_acf_v5-03/moduleTest.py#L25-L28))

Ph2_ACF links: [Ph2_ACF documentation](https://ph2acf.docs.cern.ch/general/) and [Ph2_ACF code](https://gitlab.cern.ch/cms_tk_ph2/Ph2_ACF)

## Standard module test launch
To launch the module test you need to pass `--board`, `--slot`, `--module`, and `--session` options. Example: 
```
python3 moduleTest.py --board fc7ot2 --slot 0 --module PS_26_05-IBA_00102 --session session1
```
where:
 - `--board fc7ot2` is FC7 board to be used. It uses the IP map declared in `/etc/hosts`.
 - `--slot 0` is the optical group of the FC7 board connected to the module. More infos about the optical group numbering [here](https://mattermost.web.cern.ch/cms-exp/pl/cy7r7rhcufgb3kphtx6u7a1b6e).
 - `--module PS_26_05-IBA_00102` is the name of the module which is expected to be connected
 - `--session session1` is the session name. It will be used to associated this test to a specific session. During standard operations the session will be created by [BurnIn_Controller](https://github.com/pisaoutertracker/BurnIn_Controller) (See "Test sessions" in the [TBPS database](https://cmstkita.web.cern.ch/Pisa/TBPS/localdb.html). `session1` can be used for testing)

Reminder: `python3 moduleTest.py --help`

### Quick check of connection and supply (--readOnlyID)
To verify only the module connection and supply: 
```
python3 moduleTest.py --board fc7ot2 --slot 0 --module PS_26_05-IBA_00102 --session session1 --readOnlyID
```
 - `--readOnlyID` will limit the test to read the module ID. The code will check if the module ID is already existing in the local db, and, in that case, will find the corresponding module name, and check if it matches with the module name passed with the `--module` option.

### Multiple test
You can run a test for multiple modules by passing a comma-separated list of slots and modules to `--slot` and `--module`. Example:
```
python3 moduleTest.py --board fc7ot2 --slot 0,1 --module PS_26_05-IBA_00102,PS_26_05-IPG_00102 --session session1
```

## Standard module test description
This script will:
- create a XML file, starting from [PS_Module_v2p1.xml](https://gitlab.cern.ch/cms_tk_ph2/Ph2_ACF/-/blob/Dev/settings/PS_Module_v2p1.xml?ref_type=heads), to be used in `runCalibration` according to the options passed to `python3 moduleTest.py`;
- run `fpgaconfig`;
- run `runCalibration -b -c calibrationandpedenoise -f ModuleTest_settings.xml` independently per each module;
- read the output ROOT file of each module test and:
  - check which pixel/strip worked or crashed;
  - get the lpGBT hardware ID;
  - compute the average noise of each pixel/strip chip;
- compress the configuration, ROOT file/ and logs to a single zip file
- upload the zip file, configuration (`.xml` and `.py`), ROOT file, and logs to CERN box using WebDAV ([eg. https://cernbox.cern.ch/files/link/public/zcvWnJKEk7YgSBh/T2023_11_15_15_49_36_566790](https://cernbox.cern.ch/files/link/public/zcvWnJKEk7YgSBh/T2023_11_15_15_49_36_566790))
- evaluate an outcome of the test (pass/failed) depending on the noise of the chips;
- create a webpage to show the results ([example](https://cmstkita.web.cern.ch/Pisa/TBPS/navigator.php/Uploads//test3/Module_PS_26_05-IBA_00102_Run_run386_Result_Test7/results_qdjwe.zip/));
- upload the results to the [test DB](https://cmstkita.web.cern.ch/Pisa/TBPS/ ([code](https://github.com/pisaoutertracker/testmongo)) including:
  - the outcome of the module test (pass or failed),
  - the link to the `.zip` file containing the ROOT and log files,
  - the link to the webpage.

# Advanced usage

## Additional options
- `--addNewModule`: this option will allow to add new module found to the database (without asking y/n)
- `--runFpgaConfig`: `fpgaconfig` is run automatically only when is necessary (ie. the test does not start). This option will force to run `fpgaconfig` (eg. necessary to install a new firmware);
- `--g10`: to install 10G firmware (`ps8m10gcic2l12octal8tlu.bin`) instead of 5G (`ps_twomod_oct23.bin`);
- `--localPh2ACF`: run the local Ph2_ACF without using Docker;
- `--strip`: specify which strip will be used (default `--strip 0,1,2,3,4,5,6,7`);
- `--pixel`: specify which pixel will be used (default `--pixel 8,9,10,11,12,13,14,15`);
- `--hybrid`: specify which pixel will be used (default `--hybrid 0,1`);
- `--lpGBT`: specify the lpGBT file to be used (default=lpGBT_v1_PS.txt);
- `--edgeSelect`: if defined, it will force the `edgeSelect` parameter under `<Hybrid><Global><CIC2>` in the .xml file.
- `--firmware`: specify a firmware to be installed with `fpgaconfig`
- `--ignoreConnection`: do not throw exception if there is a mismatch between the database connection and the module declared (temporary activated by default)
- many other options used for code testing (eg. `--useExistingModuleTest`, `--useExistingXmlFile`, `--skipUploadResults`, `--skipMongo`, `--skipModuleCheck`, `--xmlPyConfigFile`)

## Create a new docker version
The code uses the [docker version of Ph2_ACF](https://gitlab.cern.ch/cms_tk_ph2/docker_exploration/container_registry) (eg. `gitlab-registry.cern.ch/cms_tk_ph2/docker_exploration/cmstkph2_user_al9:ph2_acf_v5-03`), specifically the [cmstkph2_user_al9 image](https://gitlab.cern.ch/cms_tk_ph2/docker_exploration/container_registry/19856?after=MTA).
Per each offcial version of Ph2_ACF (eg. `ph2_acf_v5-03`) a new docker image is uploaded to [cms-pisa repository](https://gitlab.cern.ch/cms-pisa/PisaTracker/container_registry/19555) (eg. `gitlab-registry.cern.ch/cms-pisa/pisatracker/pisa_module_test:ph2_acf_v5-03`, which includes the compiled version of Ph2_ACF and some packages necessary to run `moduleTest.py`.

To create and upload a new docker image:

**Important: you need real Docker to run `build.sh`, not podman**, check it with `docker --version`.
```
cd buildNewDockerImage
## Edit build.sh to replace "v5-03" with a different version 
source build.sh
```

#### makeXml.py
You can also use directly
```
python3 makeXml.py
```
to create the XML file to be used in the `ot_module_test` using the configuration defined in [PS_Module_settings.py](PS_Module_settings.py).
(Check the configuration parameters)

#### docker
This code uses a Docker image created by [buildNewDockerImage/build.sh](buildNewDockerImage/build.sh);
