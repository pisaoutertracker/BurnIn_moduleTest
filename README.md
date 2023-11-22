# BurnIn_moduleTest
Run PS module test, read the output, and upload the result on MongoDB and CERN box

```
git clone https://github.com/pisaoutertracker/BurnIn_moduleTest.git
python3 moduleTest.py
```
(Check configuration parameters).

This script will:
- make a XML file to be used in `ot_module_test` using the configuration in [PS_Module_settings.py](PS_Module_settings.py);
- run `fpgaconfig`;
- run `ot_module_test`;
- read the output ROOT file to:
  - check which pixel/strip worked or crashed;
  - get the lpGBT hardware ID of each module;
  - compute the average noise of each pixel/strip chip;
- compress the ROOT file and logs to zip
- upload the zip file, ROOT file, and logs to CERN box using WebDAV ([eg. https://cernbox.cern.ch/files/link/public/zcvWnJKEk7YgSBh/T2023_11_16_16_26_27_866650](https://cernbox.cern.ch/files/link/public/zcvWnJKEk7YgSBh/T2023_11_16_16_26_27_866650))
- evaluate an outcome of the test (pass/failed) depending on the noise of the chips;
- upload the results to the [test DB](https://github.com/pisaoutertracker/testmongo) including:
  - the outcome of the module test (pass or failed),
  - the link to the `.zip` file containing the ROOT and log files.

#### makeXml.py
You can also use directly
```
python3 makeXml.py
```
to create the XML file to be used in the `ot_module_test` using the configuration defined in [PS_Module_settings.py](PS_Module_settings.py).
(Check the configuration parameters)
