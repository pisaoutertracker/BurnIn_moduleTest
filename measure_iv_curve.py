#!/usr/bin/env python3
# NOTE: upload will not work on prototype modules because of strict validation form py4dbupload; for thermal user on pccmslab1 I have fixed it locally by changing py4dbupload/modules/Utils.py line 42 to: r = re.compile('PS_(?:16|26|40)_(?:05_)?(?:IBA|IPG|BRN|FNL|DSY)-[0-9]{5}')

import sys
import select
import time
import socket
import json
from datetime import datetime
import os
import numpy as np
import argparse
import shlex
import subprocess
import tempfile
from datetime import timedelta 
from influxdb_client import InfluxDBClient 
from influxdb_client.client.write_api import SYNCHRONOUS 
INFLUX_AVAILABLE = True 
# Global variable to cache the query API object
_influx_query_api = None

# Define buffer size for TCP communication
BUFFER_SIZE = 100000 # Can be adjusted

def getInfluxQueryAPI(token_location="~/private/influx.sct", force_new=False): 
    """Gets a cached InfluxDB query API client.""" 
    global _influx_query_api 
    if not INFLUX_AVAILABLE: 
        return None 
        
    if _influx_query_api is None or force_new: 
        try: 
            token_path = os.path.expanduser(token_location) 
            if not os.path.exists(token_path): 
                 print(f"Warning: InfluxDB token file not found at {token_path}") 
                 return None 
            token = open(token_path).read().strip() 
            # TODO: Make URL and token path configurable if needed
            client = InfluxDBClient(url="http://cmslabserver:8086/", token=token) 
            _influx_query_api = client.query_api() 
            print("InfluxDB connection established.") 
        except Exception as e: 
            print(f"Warning: Failed to connect to InfluxDB - {e}") 
            _influx_query_api = None 
            
    return _influx_query_api


def get_latest_sensor_value(timestamp, sensor_field, org="pisaoutertracker", bucket="sensor_data", measurement="mqtt_consumer", lookback_window=timedelta(seconds=3)):
    """Fetches the latest sensor value from InfluxDB before a given timestamp."""
    query_api = getInfluxQueryAPI()
    if query_api is None:
        return None

    start_window = (timestamp - lookback_window).isoformat("T") + "Z"
    stop_window = timestamp.isoformat("T") + "Z"
    
    # Use sensor_field for filtering the specific sensor reading
    if not sensor_field.startswith("/fnalbox/full/"):
        query = f''' 
        from(bucket: "{bucket}")
            |> range(start: {start_window}, stop: {stop_window})
            |> filter(fn: (r) => r["_measurement"] == "{measurement}")
            |> filter(fn: (r) => r["_field"] == "{sensor_field}") 
            |> last() 
            |> yield(name: "last")
        '''
    else:
        # for /fnalbox/full/ we need to specify the topic as well
        topic, sensorName = sensor_field.rsplit("/",1)
        topicLine = f'\n                |> filter(fn: (r) => r["topic"] == "{topic}")'
        query = f'''
                from(bucket: "sensor_data")
                |> range(start: {start_window}, stop: {stop_window})
                |> filter(fn: (r) => r["_measurement"] == "{measurement}")
                |> filter(fn: (r) => r["_field"] == "{sensorName}" ){topicLine} 
                |> last()
                |> yield(name: "last")
                '''
    
    try:
        tables = query_api.query(query, org=org)
        values = [record.get_value() for table in tables for record in table.records]
        
        if values:
            # Return the single latest value found
            return values[0]
        else:
            # print(f"Warning: No data found for sensor '{sensor_field}' in the last {lookback_window.total_seconds()}s before {timestamp}") # Optional: More verbose warning
            return None
            
    except Exception as e:
        print(f"Warning: Error querying InfluxDB for sensor '{sensor_field}' - {e}")
        return None
    
# Define scan types
SCAN_CONFIGS = {
    'before_encapsulation': {'max_voltage': 350, 'step': 10},
    'after_encapsulation': {'max_voltage': 800, 'step': 10}
}

def handle_interactive_process(command, timeout=60):
    # Force unbuffered output in subprocess
    # env = os.environ.copy()
    # env['PYTHONUNBUFFERED'] = '1'
    
    process = subprocess.Popen(
        command,
        shell=True,
        executable='/bin/bash',
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
        # bufsize=1,  # Line buffering
        # env=env
    )
    
    start_time = time.time()
    output_buffer = ""
    
    while True:
        if process.poll() is not None:
            print("Process ended with code:", process.returncode)
            break
            
        if time.time() - start_time > timeout:
            process.kill()
            print("Process timed out")
            return -1
            
        reads = [process.stdout, process.stderr]
        ret = select.select(reads, [], [], 0.1)[0]
        
        for pipe in ret:
            char = pipe.read(1)
            if char:
                output_buffer += char
                print(char, end='', flush=True)  # Debug: show real-time output
                
                # if char == '\n':
                #     # Process complete line
                #     print(output_buffer)  # Debug
                #     output_buffer = ""
                    
                # Check for auth prompt at end of buffer 
                # NOTE: Not working as expected, we rely on .session.cache 
                # if output_buffer.rstrip().endswith(('Username: ', 'Password: ', 'login:')):
                #     print("\nDEBUG: Auth prompt detected:", output_buffer)  # Debug
                #     response = input("") + "\n"
                #     process.stdin.write(response)
                #     process.stdin.flush()
                #     output_buffer = ""
    
    return process.returncode

class TCPUtil():
    """Utility class for tcp communication management."""
    def __init__(self, ip, port):
        self.ip = ip
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.headerBytes = 4
        self.socket.settimeout(0.5) # Increased timeout slightly

        self.connectSocket()

    def __del__(self):
        """Destructor, closes socket"""
        try:
            self.closeSocket()
        except Exception:
            pass # Ignore errors during cleanup

    def connectSocket(self):
        """Connects socket"""
        try:
            self.socket.connect((self.ip, self.port))
        except socket.error as e:
            print(f"Error connecting socket: {e}")
            raise # Re-raise the exception

    def closeSocket(self):
        """Closes socket connection"""
        if self.socket:
            self.socket.close()
            self.socket = None # Mark as closed

    def sendMessage(self, message):
        """Encodes message and sends it on socket"""
        if not self.socket:
            print("Error: Socket is not connected.")
            return
        try:
            encodedMessage = self.encodeMessage(message)
            self.socket.sendall(encodedMessage) # Use sendall for reliability
        except socket.error as e:
            print(f"Error sending message: {e}")
            self.closeSocket() # Close socket on error
            raise # Re-raise the exception

    def receiveMessage(self):
        """Receives message from socket, handling fragmentation"""
        if not self.socket:
            print("Error: Socket is not connected.")
            return None
        
        data = b''
        try:
            while True:
                chunk = self.socket.recv(BUFFER_SIZE)
                if not chunk:
                    # Connection closed prematurely
                    print("Warning: Socket connection closed before receiving full message.")
                    break
                data += chunk

                try:
                    next_chunk = self.socket.recv(BUFFER_SIZE)
                    if not next_chunk:
                        break # Connection closed
                    data += next_chunk
                except socket.timeout:
                    break
        except socket.timeout:
            # This can happen if the server doesn't send anything
            print("Warning: Socket timeout during receive.")
            # Return whatever data we got, might be incomplete
        except socket.error as e:
            print(f"Error receiving message: {e}")
            self.closeSocket() # Close socket on error
            return None # Indicate error

        if len(data) > 8: # Check if we have at least the header
             return data[8:].decode("utf-8") # Strip header and decode
        elif len(data) > 0:
             print(f"Warning: Received incomplete data (length {len(data)})")
             return None # Indicate incomplete data
        else:
             return None # No data received

    def encodeMessage(self, message):
        """Encodes message adding 4 bytes header"""
        messageLength = len(message) + self.headerBytes + 4
        N = 0
        return (messageLength).to_bytes(4, byteorder='big') + N.to_bytes(4, byteorder='big') + message.encode('utf-8')

class IVCurveMeasurement:
    def __init__(self, channel, voltage_steps, delay=5.0, voltage_threshold=0.5, voltage_threshold_time=0.5, voltage_threshold_retries=20, settling_time=0.5, final_voltage=300):
        self.channel = channel
        self.voltage_steps = voltage_steps
        self.delay = delay
        self.voltage_threshold = voltage_threshold
        self.voltage_threshold_time = voltage_threshold_time
        self.voltage_threshold_retries = voltage_threshold_retries
        self.settling_time = settling_time
        self.measurements = []
        self.max_data_retries = 3  # Add max retries for incomplete data
        self.final_voltage = final_voltage
        
    def get_caen_data(self):
        """Get data from CAEN with retry logic for incomplete data"""
        measure_conn = None # Initialize connection variable
        for attempt in range(self.max_data_retries):
            try:
                measure_conn = TCPUtil(ip='192.168.0.45', port=7000)
                measure_conn.sendMessage('GetStatus,PowerSupplyId:caen')
                # Use the new receiveMessage method
                data_str = measure_conn.receiveMessage()
                measure_conn.closeSocket() # Close socket after receiving

                if data_str is None:
                    print(f"Attempt {attempt + 1}: Failed to receive data, retrying...")
                    time.sleep(1)
                    continue

                # Verify data integrity
                parsed_data = {}
                valid_data = True

                for token in data_str.split(','):
                    if token.startswith('caen'):
                        if ":" not in token:
                            print(f"Invalid token in attempt {attempt + 1}: {token}")
                            valid_data = False
                            break
                        key, value = token.split(":")
                        try:
                            parsed_data[key] = float(value)
                        except ValueError:
                            print(f"Invalid value in attempt {attempt + 1}: {token}")
                            valid_data = False
                            break

                if valid_data and len(parsed_data) > 0:
                    return parsed_data

                print(f"Attempt {attempt + 1}: Received invalid or incomplete data, retrying...")
                time.sleep(1)  # Wait before retry

            except (socket.error, RuntimeError, ConnectionRefusedError) as e:
                 print(f"Attempt {attempt + 1}: Communication error - {e}, retrying...")
                 if measure_conn:
                     measure_conn.closeSocket() # Ensure socket is closed on error
                 time.sleep(2) # Longer wait after communication error
                 continue
            finally:
                 # Ensure socket is closed even if parsing fails within the loop
                 if measure_conn and measure_conn.socket:
                     measure_conn.closeSocket()


        raise RuntimeError("Failed to get valid data from CAEN after maximum retries")

    def verify_voltage(self, target_voltage):
        attempt = 0
        
        while attempt < self.voltage_threshold_retries:
            try:
                parsed_data = self.get_caen_data()
                current_voltage = parsed_data[f'caen_{self.channel}_Voltage']
                # print(f"Current voltage: {current_voltage}V")
                if abs(current_voltage - target_voltage) <= self.voltage_threshold:
                    print(f"Voltage reached target value {target_voltage} V within threshold, settling...")
                    time.sleep(self.settling_time)  # Wait for settling time
                    return True
                
                time.sleep(self.voltage_threshold_time)
                attempt += 1
            except Exception as e:
                print(f"Error reading voltage: {e}")
                attempt += 1
                continue
            
        return False

    def measure_curve(self):
        on_conn = None
        voltage_conn = None
        final_conn = None
        set_final_voltage_conn = None

        try:
            # turn on channel
            print(f"Turning on channel {self.channel}")
            on_conn = TCPUtil(ip='192.168.0.45', port=7000)
            on_conn.sendMessage(f'TurnOn,PowerSupplyId:caen,ChannelId:{self.channel}')
            # Optional: receive ack if needed, but often not necessary for commands
            # ack = on_conn.receiveMessage()
            # print(f"Received acknowledgment for TurnOn: {ack}")
            on_conn.closeSocket()
            print(f"Channel {self.channel} turned on.")
            time.sleep(1) # Short delay after turning on

            for voltage in self.voltage_steps:
                print(f"Setting voltage to {voltage} V")
                try:
                    # Create new connection for voltage setting
                    voltage_conn = TCPUtil(ip='192.168.0.45', port=7000)
                    voltage_conn.sendMessage(f'SetVoltage,PowerSupplyId:caen,ChannelId:{self.channel},Voltage:{voltage}')
                    # Optional: receive ack
                    # ack = voltage_conn.receiveMessage()
                    # print(f"Received acknowledgment for SetVoltage: {ack}")
                    voltage_conn.closeSocket()
                except (socket.error, RuntimeError) as e:
                    print(f"Error setting voltage to {voltage}V: {e}. Skipping step.")
                    if voltage_conn: voltage_conn.closeSocket()
                    continue # Skip to next voltage step

                time.sleep(self.delay)  # Wait for voltage to stabilize

                # Verify voltage is within threshold
                if not self.verify_voltage(voltage):
                    print(f"Warning: Could not reach target voltage {voltage}V within threshold")
                    # Decide whether to continue or stop based on requirements
                    continue # Continue to next step for now

                try:
                    parsed_data = self.get_caen_data()
                    # --- Get Temp/Humidity Data --- 
                    now = datetime.now()
                    
                    # Attempt to get temperature (replace 'Temp0' if needed)
                    temp_value = get_latest_sensor_value(now, sensor_field="Temp0")
                    # Attempt to get humidity (replace '/ble/Sensor-2' if needed)
                    humidity_value = get_latest_sensor_value(now, sensor_field="/fnalbox/full/Humidity")
                    
                    # Use default values if InfluxDB query failed or returned no data
                    temperature = temp_value if temp_value is not None else 25.0
                    humidity = humidity_value if humidity_value is not None else 50.0
                    
                    if temp_value is None:
                        print("Warning: Using default temperature (25.0 C)")
                    if humidity_value is None:
                         print("Warning: Using default humidity (50.0 %)")
                    # --- End Get Temp/Humidity Data --- section

                    measurement = {
                        'Voltage': -parsed_data[f'caen_{self.channel}_Voltage'], # NOTE: Negative voltage for IV curve
                        'Current': parsed_data[f'caen_{self.channel}_Current'] * 1e3, # NOTE: Convert to nA assuming the readout is in uA
                        'Temperature': temperature, # Modified: Use fetched or default value
                        'Relative Humidity': humidity, # Modified: Use fetched or default value
                        'Timestamp': now.strftime('%Y-%m-%d %H:%M:%S') # Modified: Use consistent timestamp
                    }
                    self.measurements.append(measurement)
                    print(f"Measured: V={measurement['Voltage']:.2f} V, I={measurement['Current']:.3f} nA, T={measurement['Temperature']:.1f} C, RH={measurement['Relative Humidity']:.1f} %")
                except Exception as e:
                    print(f"Error during measurement or sensor reading at {voltage}V: {e}") # Modified error message slightly
                    continue

        finally:
            # Ensure all connections attempted are closed
            if on_conn and on_conn.socket: on_conn.closeSocket()
            if voltage_conn and voltage_conn.socket: voltage_conn.closeSocket()

            # Turn off channel with new connection
            try:
                print(f"Turning off channel {self.channel}")
                final_conn = TCPUtil(ip='192.168.0.45', port=7000)
                final_conn.sendMessage(f'TurnOff,PowerSupplyId:caen,ChannelId:{self.channel}')
                # Optional: receive ack
                # ack = final_conn.receiveMessage()
                # print(f"Received acknowledgment for TurnOff: {ack}")
                final_conn.closeSocket()
                print(f"Channel {self.channel} turned off.")
            except (socket.error, RuntimeError) as e:
                print(f"Error turning off channel {self.channel}: {e}")
                if final_conn: final_conn.closeSocket()

            # Set final voltage after turning off
            try:
                print(f"Setting final voltage to {self.final_voltage} V on channel {self.channel}")
                set_final_voltage_conn = TCPUtil(ip='192.168.0.45', port=7000)
                set_final_voltage_conn.sendMessage(f'SetVoltage,PowerSupplyId:caen,ChannelId:{self.channel},Voltage:{self.final_voltage}')
                # Optional: receive ack
                # ack = set_final_voltage_conn.receiveMessage()
                # print(f"Received acknowledgment for final SetVoltage: {ack}")
                set_final_voltage_conn.closeSocket()
                print(f"Final voltage set to {self.final_voltage} V.")
            except (socket.error, RuntimeError) as e:
                print(f"Error setting final voltage on channel {self.channel}: {e}")
                if set_final_voltage_conn: set_final_voltage_conn.closeSocket()


    def save_to_csv(self, output_path, run_info):
        """Save measurements to CSV file in the required format"""
        target_file = output_path
        # Create output directory if it doesn't exist
        os.makedirs(os.path.dirname(target_file), exist_ok=True)
        
        with open(target_file, 'w') as f:
            # Write header information
            f.write('#NameLabel,' + run_info.get('Module_ID', 'TEST_MODULE') + "\n")
            f.write('#Date,' + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + "\n")
            f.write("#Comment," + run_info.get('Comment', 'IV curve measurement') + "\n")
            f.write("#Location," + run_info.get('Location', 'TEST_LOCATION') + "\n")
            f.write("#Inserter," + run_info.get('Operator', 'TEST_OPERATOR') + "\n")
            f.write("#RunType," + run_info.get('Run_type', 'IV_CURVE') + "\n")
            f.write("\n")
            
            # Write temperature summary
            f.write("STATION, AV_TEMP_DEGC, AV_RH_PRCNT\n")
            if self.measurements: # avoid division by zero
                mean_temp = sum(m['Temperature'] for m in self.measurements) / len(self.measurements)
                mean_rh = sum(m['Relative Humidity'] for m in self.measurements) / len(self.measurements)
            else:
                mean_temp = -999
                mean_rh = -999
            f.write(f"{run_info.get('Station_Name', 'TEST_STATION')},{mean_temp},{mean_rh}\n\n")
            
            # Write measurement data
            f.write("VOLTS, CURRNT_NAMP, TEMP_DEGC, RH_PRCNT, TIME\n")
            for point in self.measurements:
                f.write(f"{point['Voltage']},{point['Current']},{point['Temperature']},"
                       f"{point['Relative Humidity']},{point['Timestamp']}\n")
        
        return target_file

def get_default_filename(channel, module_name, scan_type):
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    return f"IV_curve_{channel}_{module_name}_{scan_type}_{timestamp}.csv"

def measure_and_upload(
    channel,
    scan_type,
    delay=5.0,
    voltage_threshold=0.5,
    voltage_threshold_time=0.5,
    voltage_threshold_retries=20,
    settling_time=0.5,
    output_file=None,
    output_dir='./IVdata',
    module_name='TEST',
    upload=False,
    store_locally=False,
    final_voltage=300
):
    """
    Measure IV curve and optionally upload to database
    Returns: (exit_code, file_path) tuple where file_path is None if not stored locally
    """
    # Generate voltage steps based on scan type
    scan_config = SCAN_CONFIGS[scan_type]
    voltage_steps = np.arange(0, scan_config['max_voltage'] + scan_config['step'], scan_config['step'])
    
    # Configure measurement
    iv_curve = IVCurveMeasurement(
        channel=channel,
        voltage_steps=voltage_steps,
        delay=delay,
        voltage_threshold=voltage_threshold,
        voltage_threshold_time=voltage_threshold_time,
        voltage_threshold_retries=voltage_threshold_retries,
        settling_time=settling_time,
        final_voltage=final_voltage
    )
    
    # Perform measurement
    iv_curve.measure_curve()
    
    # Prepare output filename and path
    final_output_file = None
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=not store_locally) as tmp_file:
        output_path = tmp_file.name
        if store_locally:
            if output_file:
                final_output_file = output_file
            else:
                final_output_file = get_default_filename(channel, module_name, scan_type)
            final_output_path = os.path.join(output_dir, final_output_file)
        
        # Save results
        run_info = {
            "Module_ID": module_name,
            "Comment": f"{scan_type} measurement",
            "Location": "INFN Pisa",
            "Operator": os.getenv('USER', 'TEST_USER'),
            "Run_type": "IV_TEST",
            "Station_Name": "cleanroom"
        }
        
        saved_file = iv_curve.save_to_csv(output_path, run_info)
        
        if upload:
            print("Uploading to central database...")
            upload_command = f"source py4dbupload/bin/setup.sh && python3 ./py4dbupload/run/uploadOTModuleIV.py --upload --store --data={saved_file}"
            returncode = handle_interactive_process(upload_command)
            if returncode != 0:
                print("Upload failed")
                return 1
        
        if store_locally:
            os.makedirs(os.path.dirname(final_output_path), exist_ok=True)
            with open(saved_file, 'r') as src, open(final_output_path, 'w') as dst:
                dst.write(src.read())
            print(f"Measurements saved to: {final_output_path}")
    
    return 0

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='IV Curve Measurement Script')
    parser.add_argument('--channel', type=str, required=True, help='Channel ID (e.g., HV005)')
    parser.add_argument('--scan-type', type=str, choices=SCAN_CONFIGS.keys(), required=True,
                      help='Type of scan to perform')
    parser.add_argument('--delay', type=float, default=5.0,
                      help='Delay between measurements (default: 5.0s)')
    parser.add_argument('--voltage-threshold', type=float, default=0.5,
                      help='Voltage verification threshold (default: 0.5V)')
    parser.add_argument('--voltage-threshold-time', type=float, default=0.5,
                        help='Time between voltage threshold checks (default: 0.5s)')
    parser.add_argument('--voltage-threshold-retries', type=int, default=20,
                        help='Number of retries for voltage threshold check (default: 20)')
    parser.add_argument('--settling-time', type=float, default=0.5,
                      help='Settling time after reaching target voltage (default: 0.5s)')
    parser.add_argument('--output-file', type=str,
                      help='Output file path (default: auto-generated)')
    parser.add_argument('--output-dir', type=str, default='./IVdata',
                      help='Output directory (default: /IVdata in current directory)')
    parser.add_argument('--module-name', type=str, default='TEST',
                      help='Module name (default: TEST)')
    parser.add_argument('--upload', action='store_true', help='Upload to central database')
    parser.add_argument('--store-locally', action='store_true', help='Store the CSV file locally')
    parser.add_argument('--final-voltage', type=float, default=300,
                      help='Final voltage to set before turning off (default: 300V)')
    
    args = parser.parse_args()
    
    exit_code = measure_and_upload(
        channel=args.channel,
        scan_type=args.scan_type,
        delay=args.delay,
        voltage_threshold=args.voltage_threshold,
        voltage_threshold_time=args.voltage_threshold_time,
        voltage_threshold_retries=args.voltage_threshold_retries,
        settling_time=args.settling_time,
        output_file=args.output_file,
        output_dir=args.output_dir,
        module_name=args.module_name,
        upload=args.upload,
        store_locally=args.store_locally,
        final_voltage=args.final_voltage
    )
    
    print(f"Script finished with exit code: {exit_code}")
    sys.exit(exit_code)