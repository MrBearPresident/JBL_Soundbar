import asyncio
import aiohttp
import requests
import json
import logging
import urllib3
import ssl
import certifi
from datetime import timedelta
import logging


class Coordinator():
    def __init__(self):
        self.data = {}
        self.address = "192.148.4.66"
        ssl_context = ssl.create_default_context(cafile=certifi.where())
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        self.sslcontext = ssl_context
        #Setting up cert        
        cert_path = "custom_components/jbl_integration/Cert.pem"
        key_path = "custom_components/jbl_integration/Key.pem"
        self.sslcontext.load_cert_chain(certfile=cert_path, keyfile=key_path)
    
    @property
    def dataResult(self):
        return self.data 
    
    async def requestInfo(self):
        # Disable SSL warnings
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
        """Fetch data from the API."""
        url = f'http://{self.address}:59152/upnp/control/rendertransport1'
        headers = {
            "Content-type": 'text/xml;charset="utf-8"',
            "Soapaction": '"urn:schemas-upnp-org:service:AVTransport:1#GetInfoEx"'
        }
        payload = """
        <?xml version="1.0" encoding="utf-8" standalone="yes"?>
        <s:Envelope s:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/" xmlns:s="http://schemas.xmlsoap.org/soap/envelope/">
            <s:Body>
            <u:GetInfoEx xmlns:u="urn:schemas-upnp-org:service:AVTransport:1">
                <InstanceID>0</InstanceID>
            </u:GetInfoEx>
            </s:Body>
        </s:Envelope>
        """
        async with aiohttp.ClientSession() as session:
            try:
                async with asyncio.timeout(10):
                    async with session.post(url, headers=headers, data=payload) as response:
                        if response.status == 200:
                            response_text = await response.text()
                            # Parse the XML response manually, as it's not JSON
                            from xml.etree import ElementTree as ET
                            root = ET.fromstring(response_text)
                            namespaces = {
                                's': 'http://schemas.xmlsoap.org/soap/envelope/',
                                'u': 'urn:schemas-upnp-org:service:AVTransport:1'
                            }
                            try:
                                play_medium = root.find('.//u:GetInfoExResponse/PlayMedium', namespaces).text
                                volume_level = root.find('.//u:GetInfoExResponse/CurrentVolume', namespaces).text
                                track = root.find('.//u:GetInfoExResponse/TrackURI', namespaces).text
                                transport_state = root.find('.//u:GetInfoExResponse/CurrentTransportState', namespaces).text
                                transport_status = root.find('.//u:GetInfoExResponse/CurrentTransportStatus', namespaces).text
                                track_duration = root.find('.//u:GetInfoExResponse/TrackDuration', namespaces).text
                                mute = root.find('.//u:GetInfoExResponse/CurrentMute', namespaces).text
                                channel = root.find('.//u:GetInfoExResponse/CurrentChannel', namespaces).text
                                slaves = root.find('.//u:GetInfoExResponse/SlaveFlag', namespaces).text
                                gatheredData = {
                                    "play_medium": play_medium,
                                    "volume_level": volume_level,
                                    "track": track,
                                    "transport_state": transport_state,
                                    "transport_status": transport_status,
                                    "track_duration": track_duration,
                                    "mute": mute,
                                    "channel": channel,
                                    "slaves": slaves,
                                }
                                return gatheredData
                            except AttributeError:
                                return {}
                        else:
                            return {}
            except Exception as e:
                return {}

    async def getNightMode(self):
        # Disable SSL warnings
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
        url = f'https://{self.address}/httpapi.asp?command=getPersonalListeningMode'
        
        headers = {
        'Accept-Encoding': "gzip",
        }
        async with aiohttp.ClientSession() as session:
            try:
                async with asyncio.timeout(10):
                    async with session.get(url, headers=headers,  ssl=self.sslcontext) as response:
                        if response.status == 200:
                            response_text = await response.text()
                            response_json = json.loads(response_text)
                            
                            return {"NightMode":response_json.get("status", "Unavailable")}
                        else:
                            return {}
            except Exception as e:
                return {}
            
    async def setNightMode(self, value: bool):
        # Disable SSL warnings
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        """Fetch data from the API."""
        url = f'https://{self.address}/httpapi.asp'
        headers = {
        'Accept-Encoding': "gzip",
        }
        
        strvalue = 'on' if value else 'off'
        payload = 'command=setPersonalListeningMode&payload={"status":"'+strvalue+'"}'

        async with aiohttp.ClientSession() as session:
            try:
                async with asyncio.timeout(10):
                    async with session.post(url, headers=headers, data=payload,  ssl=self.sslcontext) as response:
                        if response.status != 200:
                            return {}
            except Exception as e:
                return {}


    async def getDeviceInfo(self):
        # Disable SSL warnings
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
        url = f'https://{self.address}/httpapi.asp?command=getDeviceInfo'
        headers = {
        'Accept-Encoding': "gzip",
        }
        
        async with aiohttp.ClientSession() as session:
            try:
                async with asyncio.timeout(10):
                    async with session.get(url, headers=headers,  ssl=self.sslcontext) as response:
                        if response.status == 200:
                            response_text = await response.text()
                            response_json = json.loads(response_text)
                            #_LOGGER.debug("Device Info Response text: %s", response_text)
                            #get data out of JSON
                            device_info = response_json["device_info"]
                            return device_info
                        else:
                            return {}

            except Exception as e:
                return {}

    async def getDeviceType(self):
        """Fetch data from the API."""
        url = f"http://{self.address}:59152/upnp/control/rendercontrol1"
        
        payload = """<?xml version="1.0" encoding="utf-8" standalone="yes"?>
        <s:Envelope s:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/" xmlns:s="http://schemas.xmlsoap.org/soap/envelope/">
        <s:Body>
        <u:GetControlDeviceInfo xmlns:u="urn:schemas-upnp-org:service:RenderingControl:1">
        <InstanceID>0</InstanceID></u:GetControlDeviceInfo>
        </s:Body></s:Envelope>"""
        
        headers = {
        'Content-type': "text/xml;charset=\"utf-8\"",
        'Soapaction': "\"urn:schemas-upnp-org:service:RenderingControl:1#GetControlDeviceInfo\""
        }

        try:        
            async with aiohttp.ClientSession() as session:
                async with session.post(url, data=payload, headers=headers) as response:
                    if response.status == 200:
                        response_text = await response.text()
                        
                        # Parse XML response
                        namespace = {
                            's': 'http://schemas.xmlsoap.org/soap/envelope/', 
                            'u': 'urn:schemas-upnp-org:service:RenderingControl:1'
                        }
                        from xml.etree import ElementTree as ET
                        root = ET.fromstring(response_text)
                        
                        # Find the Status element
                        status_element = root.find('.//u:GetControlDeviceInfoResponse/Status', namespace)
                        
                        if status_element is not None:
                            # Get the text content of the Status element (which is a JSON string)
                            status_json_str = status_element.text
                            
                            # Parse the JSON string into a Python dictionary
                            status_data = json.loads(status_json_str)
                            
                            # Output the status data
                            return status_data
                        else:
                            return {}
        except Exception as e:
            return {}


# main coroutine
async def main():
    # execute and await the task
    cor = Coordinator()
    data0 = await cor.requestInfo()
    cor.data.update(data0)
    data0 = await cor.getDeviceInfo()
    cor.data.update(data0)
    data0 = await cor.getDeviceType()
    cor.data.update(data0)
    
    
    
    data1 = await cor.getNightMode()
    cor.data.update(data1)
    print(cor.data)
    newValue = (cor.data.get("NightMode")!='on')
    await cor.setNightMode(newValue)
    data1 = await cor.getNightMode()
    cor.data.update(data1)
    print(cor.data)
    # newValue = (cor.data.get("NightMode")!='on')
    # await cor.setNightMode(newValue)
    # data1 = await cor.getNightMode()
    # cor.data.update(data1)
    # print(cor.data)
    
 
# enable debug logging
logging.basicConfig(level=logging.DEBUG)
# start the event loop
asyncio.run(main())