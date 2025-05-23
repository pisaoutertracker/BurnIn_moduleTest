### Code used to merge Results.root and MonitorDQM.root files for the POTATO test


from ROOT import TFile, TObject
import os
def copy_directory_contents(src_dir, dst_dir):
    """
    Recursively copy all objects from src_dir into dst_dir.
    """
    for key in src_dir.GetListOfKeys():
        key_name = key.GetName()
        obj = key.ReadObj()

        if obj.InheritsFrom("TDirectory"):
            # If the object is a subdirectory, create a matching directory in dst_dir
            dst_subdir = dst_dir.mkdir(key_name)
            # Recursively copy the subdirectory's contents
            copy_directory_contents(obj, dst_subdir)
        else:
            # For normal objects (histograms, TTrees, etc.), write them directly
            dst_dir.cd()
            obj.Write(key_name)

def mergeTwoROOTfiles(inputFileName1, inputFileName2, outputFileName):
    """
    Merge two ROOT files into a new file.
    Assuming that inputFileName1 is bigger than inputFileName2.
    The contents of inputFileName1 will be copied to the new file,
    and then the contents of inputFileName2 will be appended.
    This function will create a new file named outputFileName.
    The input files will not be modified.
    """
    
    print("Calling mergeTwoROOTfiles with inputFileName1: %s, inputFileName2: %s, outputFileName: %s" % (inputFileName1, inputFileName2, outputFileName))
    # Check if inputFileName2 exists
    if not os.path.isfile(inputFileName1):
        raise ValueError("Input file %s does not exist!" % inputFileName1)

    # Copy the first file to the output file
    os.system("cp -f %s %s" % (inputFileName1, outputFileName))

    # Check if inputFileName2 exists
    if not os.path.isfile(inputFileName2):
        raise ValueError("Input file %s does not exist!" % inputFileName2)

    # Open the input file 2
    inputFile2 = TFile.Open(inputFileName2, "READ")
    # Get the "MonitorDQM" directory from the second file
    MonitorDQM     = inputFile2.Get("Detector")


    # Open the output file
    outputFile = TFile.Open(outputFileName, "UPDATE")

    # Create a new directory in the output file
    MonitorDQM_folder = outputFile.mkdir("MonitorDQM")
    MonitorDQM_folder = MonitorDQM_folder.mkdir("Detector")

    # Copy the contents of the "MonitorDQM" directory into "MonitorDQM_folder"
    copy_directory_contents(MonitorDQM, MonitorDQM_folder)


    # Open the object Board_0/OpticalGroup_0/D_B(0)_NameId_OpticalGroup(0) from the output file
    # and the object Board_0/OpticalGroup_0/D_B(0)_NameId_OpticalGroup(0) from the input file 2
    # Get the "Board_0" directory from the output file
    print(outputFile)
    Board_0 = outputFile.Get("Detector/Board_0")
    if not Board_0:
        print()
        print("DEBUG: Board_0 not found in output file %s" % outputFileName)
        print()
        print("List of keys in output file:")
        for el in outputFile.GetListOfKeys():
            print(el.GetName())
        print()
        print("List of keys in output file Detector:")
        for el in outputFile.Get("Detector").GetListOfKeys():
            print(el.GetName())
        raise ValueError("Detector/Board_0 not found in output file %s" % outputFileName)
    print("Board_0 name: %s" % Board_0.GetName())
    print(Board_0)
    print("Board_0 keys: %s" % Board_0.GetListOfKeys())

    ## Loop over all OpticalGroup in Board_0, get the nameId from LPGBTId and convert it to the module name
    from databaseTools import makeModuleNameMapFromDB
    hwToModuleName, hwToMongoID = makeModuleNameMapFromDB()

    for key in Board_0.GetListOfKeys():
        if key.GetName().startswith("OpticalGroup"):
            og_num    = key.GetName().split("_")[-1]
            OpticalGroup = Board_0.Get(key.GetName())
            nameId    = f"D_B(0)_NameId_OpticalGroup({og_num})"
            nameObj   = OpticalGroup.Get(nameId)

            # lookup
            lpgbtId   = int(str(
                OpticalGroup.Get(
                    f"D_B(0)_LpGBTFuseId_OpticalGroup({og_num})"
                )
            ))
            if not lpgbtId:
                for el in OpticalGroup.GetListOfKeys():
                    print(el.GetName())
                raise Exception(f"LpGBTId not found for OpticalGroup {og_num} in {key.GetName()}")
            if not lpgbtId in hwToModuleName:
                for el in hwToModuleName:
                    print(el)
                raise Exception(f"LpGBTId {lpgbtId} not found in hwToModuleName")
            # get the module name from the map            
            moduleName = hwToModuleName.get(lpgbtId, "UNKNOWN")

            # set & overwrite in the right place:
            nameObj.SetString(moduleName)
            # cd into Detector/Board_0/OpticalGroup_N
            outputFile.GetDirectory(
                f"Detector/Board_0/{key.GetName()}"
            ).cd()
            nameObj.Write(nameId, TObject.kOverwrite)

            print(f"{nameId} → {nameObj.GetString()}")

    # Close the input file
    inputFile2.Close()

    # Close the output file
    outputFile.Close()


    # Loop over all keys in the second file
    

# ----------------------------------------------------------------------
# Example usage:
# ----------------------------------------------------------------------

if __name__ == "__main__":
    # Define the file names
    monitorDQMFileName = "potatoconverters/TestFiles/Run_500009/MonitorDQM_2025-03-25_17-17-32.root"
    resultsFileName    = "potatoconverters/TestFiles/Run_500009/Results.root"
    outputFileName     = "POTATO_TestOutputMerged.root"

    # Call the function to merge the two ROOT files
    mergeTwoROOTfiles(resultsFileName, monitorDQMFileName, outputFileName)
    print("Merged file created:", outputFileName)