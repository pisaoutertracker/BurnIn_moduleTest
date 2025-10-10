#!/usr/bin/env bash
set -euo pipefail

### Unset all variables that may interfere with curl
unset QUERY
unset COOKIE_HDR
unset ROOT_FILE_ADDRESS
rm -f query_code.txt query_output.xml

# Usage: ./downloadRootFileFromCentralDB.sh <ROOT_FILE>
ROOT_FILE="${1:-}"
if [[ -z "$ROOT_FILE" ]]; then
  echo "ERROR: Usage: $0 <ROOT_FILE>"
  exit 1
fi

# Track if we already tried to renew the session
SESSION_RENEWED="${SESSION_RENEWED:-false}"

#export ROOT_FILE="PS_40_FNL-10059_2025-10-08_09h32m32s_+26C_PSquickTest_v6-18.root"
export QUERY="SELECT t.ROOT_BLOB FROM trker_cmsr.c18600 t WHERE t.ROOT_FILE='$ROOT_FILE'"
export COOKIE_HDR=$(jq -r '.cookies | to_entries | map("\(.key)=\(.value)") | join("; ")' .session.cache)

echo "Query: "$QUERY" using https://cmsdca.cern.ch/trk_rhapi/query?"

curl -X POST 'https://cmsdca.cern.ch/trk_rhapi/query?' \
     -H "Cookie: $COOKIE_HDR" \
     -H 'Accept: text/xml' \
     -d "$QUERY" \
     --insecure --silent > query_code.txt

if grep -q "The document has moved" query_code.txt; then
    if [[ "$SESSION_RENEWED" == "false" ]]; then
        echo "ERROR: Session expired, attempting to renew .session.cache by running python3 login.py"
        python3 login.py
        if [[ $? -eq 0 ]]; then
            echo "Session renewed successfully. Retrying the script..."
            export SESSION_RENEWED=true
            exec "$0" "$@"
        else
            echo "ERROR: Failed to renew session with python3 login.py"
            exit 1
        fi
    else
        echo "ERROR: Session expired again after renewal. Please check your credentials."
        exit 1
    fi
fi

echo ""
echo "Cookies are ok. Obtained query code:"
cat  query_code.txt
echo ""

echo "Trying to get the query result from https://cmsdca.cern.ch/trk_rhapi/query/"$(<query_code.txt)/data?""

MAX_RETRIES=3
RETRY_COUNT=0

while [[ $RETRY_COUNT -lt $MAX_RETRIES ]]; do
     unset ROOT_FILE_ADDRESS
     curl -X GET 'https://cmsdca.cern.ch/trk_rhapi/query/'$(<query_code.txt)'/data?' \
           -H "Cookie: $COOKIE_HDR" \
           -H 'Accept: text/xml' \
           --insecure --silent > query_output.xml
     ROOT_FILE_ADDRESS=$(sed -n 's:.*<ROOT_BLOB>\(.*\)</ROOT_BLOB>.*:\1:p' query_output.xml) || true

     echo ""
     echo "Response:"
     cat query_output.xml || true

     # Check if we got a proxy error or empty ROOT_FILE_ADDRESS
     HAS_PROXY_ERROR=false
     grep -qi "proxy server could not handle the request" query_output.xml 2>/dev/null && HAS_PROXY_ERROR=true || true
     
     if [[ "$HAS_PROXY_ERROR" == "true" ]] || [[ -z "${ROOT_FILE_ADDRESS:-}" ]]; then
          echo ""
          ((RETRY_COUNT++)) || true
          echo "ERROR: The query failed or ROOT_FILE_ADDRESS is empty. Retrying... (Attempt $RETRY_COUNT/$MAX_RETRIES)"
          echo ""
          sleep 2
     else
          echo ""
          echo "Query completed successfully."
          echo ""
          break
     fi
done

if [[ $RETRY_COUNT -eq $MAX_RETRIES ]]; then
     echo "ERROR: The query failed after $MAX_RETRIES retries. See the link above for details."
     exit 1
fi

echo ""
echo "Query is succesful. Downloading ROOT file from $ROOT_FILE_ADDRESS to $ROOT_FILE"

curl -X GET $ROOT_FILE_ADDRESS \
     -H "Cookie: $COOKIE_HDR" \
     -H 'Accept: text/xml' \
     --insecure --silent > $ROOT_FILE

echo ""
echo 'https://cmsdca.cern.ch/trk_rhapi/query/'$(<query_code.txt)'/data?'
cat  query_output.xml

## if file size is >1 kB, we assume it is ok
if [[ ! -s $ROOT_FILE || $(stat -c%s "$ROOT_FILE") -lt 1024 ]]; then
  echo "ERROR: downloaded ROOT file is empty or too small"
  echo ""
  cat $ROOT_FILE
  echo ""
  exit 1
fi
echo "Downloaded ROOT file $ROOT_FILE successfully"