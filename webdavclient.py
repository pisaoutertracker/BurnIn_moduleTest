import requests
import pprint
import hashlib
import xmltodict
import datetime
import os

#verbose = False
verbose = True


class WebDAVWrapper:
    def __init__(self, url, hash_value_read, hash_value_write):
        self.url = url
        self.hash_value_read = hash_value_read
        self.hash_value_write = hash_value_write
        self.completeurl_write = url+"/"+hash_value_write+"/"
        self.completeurl_read = url+"/"+hash_value_read+"/"
        if verbose: 
            print ("Configured Write: ", self.completeurl_write)
            print ("Configured Read : ", self.completeurl_read)

    def list_files(self, remote_path):
        response = self._send_request_read('PROPFIND', remote_path)
        if response.ok == False:
            print ("Error listing files")
            return False
        files = xmltodict.parse(response.text, dict_constructor=dict)
        # parse files
#        pp = pprint.PrettyPrinter(indent=3)
#        pp.pprint(files)
        allfiles = []
        for it in files[u'd:multistatus'][u'd:response']:
#            print ("ITER", it[u'd:href'])
            allfiles.append((it[u'd:href'].split(self.hash_value_read)[-1],it[u'd:propstat'][u'd:prop'][u'd:getlastmodified']))
        return allfiles

    def find_last_file(self, remote_path):
        # strip last field
        if verbose:
            print ("REMOTE PATH :", remote_path)
        remote_dir = "/"+"/".join(remote_path.split("/")[:-1])
        filename = remote_path.split(self.hash_value_read)[-1]
        if verbose:
            print ("REMOTE DIR :", remote_dir)
            print ("FILENAME   :", filename)
        files = self.list_files(remote_dir)
        filenamee = ""
        newest = datetime.datetime.strptime('Wed, 08 Nov 2023 20:06:10 GMT', "%a, %d %b %Y %H:%M:%S %Z")
        for it in files:
 #           print ("IT:", it, it[0], filename)
            name1_, extension1 = os.path.splitext(it[0])
            name1 = name1_[:-6]
            name2, extension2 = os.path.splitext(filename)
            if name1+extension1 == name2+extension2:
#                print ("COMPARE: ",newest, it[1] )
                if datetime.datetime.strptime(it[1],"%a, %d %b %Y %H:%M:%S %Z") > newest:
                    newest  = datetime.datetime.strptime(it[1],"%a, %d %b %Y %H:%M:%S %Z")
                    filenamee = it[0]
        if verbose:
            print ("FILENAME FOUND: ",filenamee)
        return filenamee

    
    def write_file (self, local_path, remote_path):
        url = self.completeurl_write+remote_path
        if verbose:
            print ("LOCAL      :",local_path)
            print ("REMOTE     :", url)
            print ("REMOET PATH:",remote_path)
        response = requests.put(url, data = open (local_path,"rb").read())
        if response.ok == False:
            print ("LOCAL      :",local_path)
            print ("REMOTE     :", url)
            print ("REMOET PATH:",remote_path)
            print(requests)
            print(response)
            print ("Error writing file")
            print ("HTTP Status Code:", response.status_code)
            if response.status_code == 409:
                print ("ERROR: 409 Conflict - The parent directory likely doesn't exist.")
                print ("Make sure to call mkDir() for the parent directory before writing the file.")
            return False
        # search back the file
        res2 = self.find_last_file(remote_path)
        return res2
    
    def download_file(self, remote_path, local_path):
        if verbose:
            print("COMPLETE      :",self.completeurl_read)
            print("REMOTE_PATH   :",remote_path)
            print("LOCAL_PATH    :", local_path)
            url = self.completeurl_read+remote_path
            print("URL           :", url)
        response = self._send_request_read('GET', remote_path)
        # Write the response content to a local file
        with open(local_path, 'wb') as local_file:
            local_file.write(response.content)
        return local_path

    def mkDir(self, remote_path):
        if verbose:
            print("REMOTE_PATH   :",remote_path)
        response = self._send_request_write('MKCOL', remote_path)
        if verbose:
            print("RESPONSE", response)
        if response.status_code == 201:
            print("Directory created successfully:", remote_path)
        elif response.status_code == 405:
            print("Directory already exists:", remote_path)
        elif response.status_code == 403:
            print("ERROR 403 Forbidden: Cannot create directory at", remote_path)
            print("Possible reasons:")
            print("  - No permission to create directories at root level")
            print("  - Write token doesn't have sufficient permissions")
            print("  - Try creating subdirectory in an existing folder (e.g., /pippo/newdir)")
        elif response.status_code == 409:
            print("ERROR 409 Conflict: Parent directory doesn't exist for", remote_path)
        return response

    def mkDirs(self, remote_path):
        """
        Create directory recursively, creating all parent directories if needed.
        Similar to mkdir -p
        """
        if verbose:
            print("mkDirs REMOTE_PATH:", remote_path)
        
        # Split path and create each level
        parts = [p for p in remote_path.split('/') if p]  # Remove empty parts
        current_path = ""
        
        for part in parts:
            current_path = current_path + "/" + part
            if verbose:
                print("Creating directory:", current_path)
            response = self._send_request_write('MKCOL', current_path)
            # 405 means directory already exists, which is OK
            if response.status_code not in [201, 405]:
                if verbose:
                    print(f"Warning: Could not create {current_path}, status: {response.status_code}")
        
        return response

    def test_permissions(self):
        """
        Test what permissions this token has
        """
        print("\n=== Testing WebDAV Permissions ===")
        print("Read URL:", self.completeurl_read)
        print("Write URL:", self.completeurl_write)
        
        # Test read
        print("\n1. Testing READ permission:")
        try:
            files = self.list_files("/")
            print("   ✓ Can list root directory")
        except:
            print("   ✗ Cannot list root directory")
        
        # Test write file
        print("\n2. Testing WRITE FILE permission:")
        test_file = "/test_permission_" + datetime.datetime.now().strftime("%Y%m%d_%H%M%S") + ".txt"
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("test")
            temp_path = f.name
        
        url = self.completeurl_write + test_file
        response = requests.put(url, data=open(temp_path, "rb").read())
        if response.status_code in [201, 204]:
            print(f"   ✓ Can write files (status {response.status_code})")
        else:
            print(f"   ✗ Cannot write files (status {response.status_code})")
        
        # Test create directory
        print("\n3. Testing CREATE DIRECTORY permission:")
        test_dir = "/test_dir_" + datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        response = self._send_request_write('MKCOL', test_dir)
        if response.status_code in [201]:
            print(f"   ✓ Can create directories (status {response.status_code})")
        elif response.status_code == 403:
            print(f"   ✗ Cannot create directories - 403 Forbidden")
            print("   → Your write token has restricted permissions")
            print("   → Contact CERNBox admin or recreate share with 'Upload/Edit' permissions")
        else:
            print(f"   ? Unexpected status: {response.status_code}")
        
        print("\n=== End Permission Test ===\n")

    def _send_request_write(self, method, remote_path):
        url = self.completeurl_write+remote_path
        if verbose:
            print ("URL", url)
        response = requests.request(method, url)
        if verbose:
            print ("RESPONSE", response)
        return response

    def _send_request_read(self, method, remote_path):
        url = self.completeurl_read+remote_path
        if verbose:
            print ("UUURL", url)
        response = requests.request(method, url)
#        print (response.text)
        return response

# Example usage
if __name__ == "__main__":

    hash_value_location = "~/private/webdav.sct" #echo "xxxxxxxxxxxxxxx|xxxxxxxxxxxxxxx" > ~/private/webdav.sct
    #hash_value_read, hash_value_write = open(os.path.expanduser(hash_value_location)).read()[:-1].split("\n")[0].split("|")
    hash_value_read, hash_value_write = open(os.path.expanduser(hash_value_location)).read()[:-1].split("\n")[1].split("|")

    webdav_url = "https://cernbox.cern.ch/remote.php/dav/public-files"
    #hash_value_read  = "XXXXXXXXXXXXXXX"  
    #hash_value_write = "XXXXXXXXXXXXXXX"
    remote_dir = "pippo"
    remote_path = "pippo/pippo2.txt" ## the folder must be already existing
    local_path = "webdavclient.py"

    webdav_wrapper = WebDAVWrapper(webdav_url, hash_value_read, hash_value_write)

    # Test permissions first
    webdav_wrapper.test_permissions()

    # List files in the remote directory
    files = webdav_wrapper.list_files(remote_dir)
    print("Files in remote directory:")
    print(files)
    1/0

# Write file ang det back real name
    print ("WRITING FILE NAME: ", local_path)
    newfile = webdav_wrapper.write_file(local_path, remote_path)
    print ("WRITTEN FILE NAME: ", newfile)
    
#read file
    print("READ FILE")
    remote_file = newfile
    new_local_file = "a3a.b5b"
    file = webdav_wrapper.download_file(remote_file,new_local_file)

#mkdir
    print("\n=== Testing mkDir ===")
    print("First, let's see what's at root:")
    root_files = webdav_wrapper.list_files("/")
    print("Root directory contents:")
    for f in root_files[:5]:  # Show first 5
        print("  ", f[0])
    
    print("\nTrying to create directory at root level (this will likely fail):")
    dname = "/PAPERINO3"
    dir = webdav_wrapper.mkDir(dname)
    
    print("\nTrying to create directory inside /pippo/ (this should work):")
    dname = "/pippo/PAPERINO3"
    dir = webdav_wrapper.mkDir(dname)


