import json
import ssl
import certifi
import urllib3
import requests

# Create an SSL context
ssl_context = ssl.create_default_context(cafile=certifi.where())
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

# Load certificate and key
cert_path = "custom_components/jbl_integration/Cert.pem"
key_path = "custom_components/jbl_integration/Key.pem"
ssl_context.load_cert_chain(certfile=cert_path, keyfile=key_path)

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Target URL and headers
url = 'https://192.148.4.66/httpapi.asp?command=getEQList'
url2 = 'https://192.148.4.66/httpapi.asp?command=getEQ'
headers = {
    'Accept-Encoding': "gzip",
}

# Perform HTTPS GET request
try:
    #response = requests.get(url, headers=headers, verify=False, cert=(cert_path, key_path))
    #print("Response Status Code:", response.status_code)
    #print("Response Body:", response.text)
    response = requests.get(url2, headers=headers, verify=False, cert=(cert_path, key_path))
    
    response_json = json.loads(response.text)
    
    #get data out of JSON
    gain = response_json["eq_setting"]["eq_payload"]["gain"]
    gatheredData = {
        "EQ_1_Low": gain[0],
        "EQ_2_Mid": gain[1],
        "EQ_3_High": gain[2]
    }
    print("Response Status Code:", gatheredData)
    #print("Response Body:", response.text)
except requests.exceptions.RequestException as e:
    print("Error during the request:", e)
