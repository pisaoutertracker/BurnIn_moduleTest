### Code used to merge Results.root and MonitorDQM.root files for the POTATO test


from ROOT import TFile
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
    # Copy the first file to the output file
    os.system("cp -f %s %s" % (inputFileName1, outputFileName))

    # Open the input file 2
    inputFile2 = TFile.Open(inputFileName2, "READ")
    # Get the "MonitorDQM" directory from the second file
    MonitorDQM     = inputFile2.Get("Detector")


    # Open the output file
    outputFile = TFile.Open(outputFileName, "UPDATE")

    # Create a new directory in the output file
    MonitorDQM_folder = outputFile.mkdir("MonitorDQM")

    # Copy the contents of the "MonitorDQM" directory into "MonitorDQM_folder"
    copy_directory_contents(MonitorDQM, MonitorDQM_folder)

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