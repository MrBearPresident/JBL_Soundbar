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
url = "https://192.148.4.66/httpapi.asp"
eqList = {
            "125Hz":0,  #Min -6, Max 6, step 0.5
            "250Hz":0,  #Min -6, Max 6, step 0.5
            "500Hz":0,  #Min -6, Max 6, step 0.5
            "1000Hz":0, #Min -6, Max 6, step 0.5
            "2000Hz":0, #Min -6, Max 6, step 0.5
            "4000Hz":0, #Min -6, Max 6, step 0.5
            "8000Hz":0, #Min -6, Max 6, step 0.5
          } 
payload = "command=setActiveEQ&payload={\"active_eq_id\":\"0\",\"band\":7,\"eq_payload\":{\"fs\":[125.0,250.0,500.0,1000.0,2000.0,4000.0,8000.0],\"gain\":[125Hz,250Hz,500Hz,1000Hz,2000Hz,4000Hz,8000Hz]}}"

for key in eqList.keys():
    payload = payload.replace(key,str(eqList.get(key)))


headers = {
    'Accept-Encoding': "gzip",
}

# Perform HTTPS GET request
try:
    #response = requests.get(url, headers=headers, verify=False, cert=(cert_path, key_path))
    #print("Response Status Code:", response.status_code)
    #print("Response Body:", response.text)
    response = requests.post(url, headers=headers,data=payload, verify=False, cert=(cert_path, key_path))

    
    #get data out of JSON
    #print("Response Status Code:", response.text)
    print("Response Body:", response.text)
except requests.exceptions.RequestException as e:
    print("Error during the request:", e)
