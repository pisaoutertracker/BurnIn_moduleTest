import importlib.util
import sys, os

## take --getSessionCacheLocation argument
verbose = 0
getSessionCacheLocation = "/home/thermal/potato/get_session_cache.py"
coockiesOutput = ".session.cache"
for i, arg in enumerate(sys.argv):
    if arg == "--getSessionCacheLocation" and i + 1 < len(sys.argv):
        getSessionCacheLocation = sys.argv[i + 1]
    if arg == "--verbose" and i + 1 < len(sys.argv):
        verbose = int(sys.argv[i + 1])
    if arg == "--coockiesOutput" and i + 1 < len(sys.argv):
        coockiesOutput = sys.argv[i + 1]

# Import the module with hyphens in the filename
spec = importlib.util.spec_from_file_location("get_session_cache", getSessionCacheLocation)
get_session_cache = importlib.util.module_from_spec(spec)
spec.loader.exec_module(get_session_cache)

# Now you can use the UpleggerSSO class
sso = get_session_cache.UpleggerSSO()

# Example usage - you'll need to provide the actual parameters

# If you need to use loginDialog, you'll need to define it first
# For now, here's a basic example with placeholder values:
##url = "https://cmsomsdet.cern.ch/tracker-resthub/query"
url = "https://cmsdca.cern.ch/trk_loader/trker/int2r"
login_type = "simple"  # Changed from "normal" to "simple" 
username = "cmspisa"
## read password from file
passwordPosition = "~/private/.cmspi"
with open(os.path.expanduser(passwordPosition), 'r') as file:
    password = file.read().strip() 
otp = None
#otp = "your_otp_if_using_2fa"

try:
    print(f"Attempting login with:")
    print(f"  URL: {url}")
    print(f"  Login type: {login_type}")
    print(f"  Username: {username}")
    print(f"  Password length: {len(password)}")
    
    cookies = sso.login_sign_on(url, login_type, username, password, otp=None) #, otp, cache_file=".session.cache", force_level=2)
    print("Login successful")
    if verbose>100:
        print(f"Cookies: {cookies}")
except Exception as e:
    print(f"Login failed with error: {e}")
    print(f"Error type: {type(e).__name__}")
    cookies = None

if cookies:
    ## Save cookies to a file or use them as needed
    with open(coockiesOutput, "w") as f:
        import json
        f.write(json.dumps({"cookies": cookies}))
        print(f"Cookies saved to {coockiesOutput}")
        f.close()
else:
    print()
    print("ERROR [login.py]: Unable to login, cookies not retrieved.")
    print()
# 
# cookies = sso.login_sign_on(url, login_type, username, password, otp)
# print("Login successful, cookies:", cookies)

#cgetSessionCache(loginDialog.getUsername(), loginDialog.getPassword(), loginDialog.use2FA(), loginDialog.getOTP()))
