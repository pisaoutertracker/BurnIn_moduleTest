# for uploading module test results to the central database
# example usage:
# python3 upload_module_test.py --module-id=PS_26_DSY-20003 --location=KIT --root-file=/home/thermal/BurnIn_moduleTest/Results/Run_500159/Results.root --upload 


import argparse
import os
import sys
import subprocess
import yaml
import tempfile
from datetime import datetime

# Import required modules for the main script
import time
import select

class DBManager:
    def run_command(self, cmd, verbose=True):
        """Run a shell command and return the return code"""
        process = subprocess.Popen(
            cmd, 
            shell=True, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE
        )
        stdout, stderr = process.communicate()
        
        if verbose:
            if stdout:
                print(stdout.decode())
            if stderr:
                print(stderr.decode())
                
        return process.returncode
        
    def createModuleTestCSV(self, pRun, pDataFile, pDirectory, temperatures=None):
        """Create a CSV file for module test data"""
        # Create a unique filename based on date and module ID
        date_part = datetime.strptime(pRun.runInfo["Date"], '%d-%m-%Y %H:%M:%S').strftime('%Y%m%d_%H%M%S')
        module_id = pRun.runInfo["Module_ID"].replace(" ", "_").replace("/", "-")
        db_file = f"ModuleTest_{module_id}_{date_part}.csv"
        
        targetFile = pDirectory + db_file
        rootFile = pDataFile["FileName"]
        pDataFile["DBFile"] = db_file   

        rh_mean = ""
        t_mean = ""
        
        # Calculate mean temperature from provided list
        if temperatures:
            try:
                t_mean = sum([float(temp) for temp in temperatures])/len(temperatures)
            except (ValueError, TypeError):
                t_mean = ""

        f = open(targetFile, 'w')

        date = datetime.strptime(pRun.runInfo["Date"],'%d-%m-%Y %H:%M:%S').strftime('%Y-%m-%d %H:%M:%S')

        f.write('#NameLabel,'   + pRun.runInfo["Module_ID"] + "\n")
        f.write('#Date,'        + date   + "\n")
        f.write("#Comment,"     + pDataFile["Comment"] + "\n")
        f.write("#Location,"    + pRun.runInfo["Location"]+ "\n")
        f.write("#Inserter,"    + pRun.runInfo["Operator"]+ "\n")
        f.write("#RunType,"     + pRun.runInfo["Run_type"]+ "\n")
        f.write("\n")

        f.write("ROOT_FILE, ROOT_DATE, ROOT_VER, ROOT_CONF_VER, ROOT_TEMP_DEGC,ROOT_CAL_NAME"+ "\n")
        try:
            f.write(rootFile + "," +  date + ", v1-00, v1-00,{:.2f}".format(t_mean) + "," + pRun.runInfo["Ph2_ACF_Test"])
        except ValueError:
            f.write(rootFile + "," +  date + ", v1-00, v1-00," + str(t_mean) + "," + pRun.runInfo["Ph2_ACF_Test"])

        f.close()


class RunInfo:
    def __init__(self, module_id, date, location, operator, run_type, ph2_acf_test):
        self.runInfo = {
            "Module_ID": module_id,
            "Date": date,
            "Location": location,
            "Operator": operator,
            "Run_type": run_type,
            "Ph2_ACF_Test": ph2_acf_test
        }

def handle_interactive_process(command, timeout=60):
    """Handle interactive process with proper input/output handling"""
    print(f"Running command: {command}")
    
    process = subprocess.Popen(
        command,
        shell=True,
        executable='/bin/bash',
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
    )
    
    start_time = time.time()
    output_buffer = ""
    stdout_buffer = ""
    stderr_buffer = ""
    
    while True:
        if process.poll() is not None:
            # Capture any remaining output
            stdout_data, stderr_data = process.communicate()
            stdout_buffer += stdout_data
            stderr_buffer += stderr_data
            print(f"Process ended with code: {process.returncode}")
            if process.returncode != 0:
                print("--- STDOUT ---")
                print(stdout_buffer)
                print("--- STDERR ---")
                print(stderr_buffer)
                print("-------------")
            break
            
        if time.time() - start_time > timeout:
            process.kill()
            print("Process timed out")
            stdout_data, stderr_data = process.communicate()
            print("--- STDOUT at timeout ---")
            print(stdout_buffer + stdout_data)
            print("--- STDERR at timeout ---")
            print(stderr_buffer + stderr_data)
            return -1
            
        reads = [process.stdout, process.stderr]
        ret = select.select(reads, [], [], 0.1)[0]
        
        for pipe in ret:
            char = pipe.read(1)
            if char:
                output_buffer += char
                if pipe == process.stdout:
                    stdout_buffer += char
                else:
                    stderr_buffer += char
                print(char, end='', flush=True)
    
    return process.returncode

def create_and_upload_module_test(
    module_id,
    root_file,
    temperatures=None,
    output_dir="./ModuleTestData",
    comment="Module Test",
    location="Pisa",
    operator=None,
    run_type="MODULE_TEST",
    ph2_acf_test="CalibrationTest",
    upload=False,
    store_locally=False,
    use_dev=False
):
    """Create and upload module test data
    
    Args:
        module_id: Module ID
        root_file: Path to the root file
        temperatures: List of temperature values
        output_dir: Output directory for the CSV file
        comment: Comment for the test
        location: Location of the test
        operator: Operator performing the test
        run_type: Type of run
        ph2_acf_test: Ph2 ACF test type
        upload: Whether to upload to the database
        store_locally: Whether to store the CSV file locally
        use_dev: Use development database instead of production
        
    Returns:
        exit_code: Exit code from the operation
    """
    if operator is None:
        operator = os.getenv('USER', 'TEST_USER')
        
    if temperatures is None:
        temperatures = [21.0, 21.5, 22.0]  # Default temperature values
        
    # Create directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Set up run info
    date_str = datetime.now().strftime('%d-%m-%Y %H:%M:%S')
    run_info = RunInfo(module_id, date_str, location, operator, run_type, ph2_acf_test)
    
    # Set up data file info
    data_file = {
        "FileName": os.path.basename(root_file),
        "Comment": comment
    }
    
    working_dir = output_dir
        
    # Create database
    db = DBManager()
    db.createModuleTestCSV(run_info, data_file, working_dir + '/', temperatures)
    
    # Get the file path
    csv_file = working_dir + '/' + data_file["DBFile"]
    
    # Upload if requested
    if upload:
        print(f"Uploading {csv_file} to database...")
        print(f"Root file: {root_file}")
        
        # Check if the necessary files and directories exist
        if not os.path.exists(csv_file):
            print(f"ERROR: CSV file does not exist: {csv_file}")
            return 1
            
        if root_file and not os.path.exists(root_file):
            print(f"ERROR: ROOT file does not exist: {root_file}")
            return 1
            
        if not os.path.exists("py4dbupload"):
            print("ERROR: py4dbupload directory not found in current path")
            print(f"Current directory: {os.getcwd()}")
            print(f"Directory contents: {os.listdir('.')}")
            return 1
            
        # Create upload command
        upload_command = f"source py4dbupload/bin/setup.sh && python3 ./py4dbupload/run/uploadOTModuleTestRootFile.py --upload --data={csv_file}"
        if store_locally:
            upload_command += " --store"
        if root_file:
            upload_command += f" --root={root_file}"
        if use_dev:
            upload_command += " --dev"
            
        return_code = handle_interactive_process(upload_command)
        
        if return_code != 0:
            print("Upload failed")
            return 1
            
    return 0
    
    
if __name__ == "__main__":


    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Module Test Upload Script')
    parser.add_argument('--module-id', type=str, required=True, help='Module ID')
    parser.add_argument('--root-file', type=str, required=True, help='Path to ROOT file')
    parser.add_argument('--temperatures', type=float, nargs='+', help='List of temperature values (default: [21.0, 21.5, 22.0])')
    parser.add_argument('--output-dir', type=str, default='./ModuleTestData', help='Output directory (default: ./ModuleTestData)')
    parser.add_argument('--comment', type=str, default='Module Test', help='Comment for test')
    parser.add_argument('--location', type=str, default='Pisa', help='Test location')
    parser.add_argument('--operator', type=str, help='Operator performing the test (default: current user)')
    parser.add_argument('--run-type', type=str, default='MODULE_TEST', help='Type of run')
    parser.add_argument('--ph2-acf-test', type=str, default='CalibrationTest', help='Ph2 ACF test type')
    parser.add_argument('--upload', action='store_true', help='Upload to central database')
    parser.add_argument('--store-locally', action='store_true', help='Store the CSV file locally')
    parser.add_argument('--use-dev', action='store_true', help='Use development database')
    
    args = parser.parse_args()
    
    # Execute the main function
    exit_code = create_and_upload_module_test(
        module_id=args.module_id,
        root_file=args.root_file,
        temperatures=args.temperatures,
        output_dir=args.output_dir,
        comment=args.comment,
        location=args.location,
        operator=args.operator,
        run_type=args.run_type,
        ph2_acf_test=args.ph2_acf_test,
        upload=args.upload,
        store_locally=args.store_locally,
        use_dev=args.use_dev
    )
    
    print(f"Script finished with exit code: {exit_code}")
    sys.exit(exit_code)