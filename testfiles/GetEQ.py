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
headers = {
    'Accept-Encoding': "gzip",
}

# Perform HTTPS GET request
try:
    #response = requests.get(url, headers=headers, verify=False, cert=(cert_path, key_path))
    #print("Response Status Code:", response.status_code)
    #print("Response Body:", response.text)
    response = requests.get(url, headers=headers, verify=False, cert=(cert_path, key_path))
    
    response_json = json.loads(response.text)
    
    #get data out of JSON
    gain = response_json["eq_list"][4]["eq_payload"]["gain"]
    eqList = {
            "125Hz":gain[0],    #Min -9, Max 6, step 0.5
            "250Hz":gain[1],    #Min -6, Max 6, step 0.5
            "500Hz":gain[2],    #Min -6, Max 6, step 0.5
            "1000Hz":gain[3],   #Min -6, Max 6, step 0.5
            "2000Hz":gain[4],   #Min -6, Max 6, step 0.5
            "4000Hz":gain[5],   #Min -6, Max 6, step 0.5
            "8000Hz":gain[6],   #Min -6, Max 6, step 0.5
          } 
    print("Response Status Code:", eqList)
    #print("Response Body:", response.text)
except requests.exceptions.RequestException as e:
    print("Error during the request:", e)
