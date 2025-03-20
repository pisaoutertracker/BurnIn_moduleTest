import requests
import pprint
import hashlib
import xmltodict
import datetime
import os

verbose = False
#verbose = True


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
        return response

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
    hash_value_read, hash_value_write = open(os.path.expanduser(hash_value_location)).read()[:-1].split("\n")[0].split("|")
    #hash_value_read, hash_value_write = open(os.path.expanduser(hash_value_location)).read()[:-1].split("\n")[1].split("|")

    webdav_url = "https://cernbox.cern.ch/remote.php/dav/public-files"
    #hash_value_read  = "XXXXXXXXXXXXXXX"  
    #hash_value_write = "XXXXXXXXXXXXXXX"
    remote_dir = "pippo"
    remote_path = "pippo/pippo2.txt" ## the folder must be already existing
    local_path = "webdavclient.py"

    webdav_wrapper = WebDAVWrapper(webdav_url, hash_value_read, hash_value_write)

    # List files in the remote directory
    files = webdav_wrapper.list_files(remote_dir)
    print("Files in remote directory:")
    print(files)

# Write file ang det back real name
    print ("WRITING FILE NAME: ", local_path)
    newfile = webdav_wrapper.write_file(local_path, remote_path)
    print ("WRITTEN FILE NAME: ", newfile)
    
#read file
    print("READ FILE")
    remote_file = newfile
    new_local_file = "aaa.bbb"
    file = webdav_wrapper.download_file(remote_file,new_local_file)

#mkdir
    dname = "/pippo/PAPERINO2"
    dir = webdav_wrapper.mkDir(dname)


