"""Sensor platform for JBL integration."""
import aiohttp
import async_timeout
import requests
import json
import logging
import urllib3
import ssl
import certifi
from datetime import timedelta
from homeassistant.helpers.entity import Entity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator


from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

class Coordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the API."""

    def __init__(self, address, pollingRate, hass=None, entry=None):
        """Initialize the coordinator."""
        self.address = address
        self.pollingRate = pollingRate
        self.data = {}
        if hass != None and entry != None:
            self._entry = entry
            self.hass = hass
            ssl_context = ssl.create_default_context(cafile=certifi.where())
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            self.sslcontext = ssl_context
            super().__init__(
                hass,
                _LOGGER,
                name="JBL Sensor",
                update_method=self._async_update_data,
                update_interval=timedelta(seconds=pollingRate),
            ) 


    async def _SetupDeviceInfo(self):
        #Setting up cert        
        cert_path = self.hass.config.path("custom_components/jbl_integration/Cert.pem")
        key_path = self.hass.config.path("custom_components/jbl_integration/Key.pem")
        self.sslcontext.load_cert_chain(certfile=cert_path, keyfile=key_path)
        
        device_info = await self.getDeviceInfo()
        device_Type = await self.getDeviceType() 


            
        # Ensure device_info has all the expected keys and provide fallback values if necessary
        mac_address = device_info.get("wlan0_mac", "unknown_mac")
        uuid = device_info.get("uuid", "unknown_uuid")
        device_name = device_info.get("name", "Unknow_name")
        serial_number = device_info.get("serial_number", "unknown_serial")
        firmware_version = device_info.get("firmware", "unknown_firmware")
        ip_address = device_info.get("apcli0", "unknown_address")
        model = device_Type.get("hm_product_name", "unknown_product")
        hw_version = device_Type.get("hardware", "unknown_hardware")

        
        self._device_info = {
            "identifiers": {
                (DOMAIN, self._entry.entry_id),
                (DOMAIN, mac_address,uuid),
                (DOMAIN, str(uuid).replace("-", "")),
                (DOMAIN, self.address),
                },
            "name": device_name,
            "manufacturer": "HARMAN International Industries",
            "model": model,
            "hw_version": hw_version,
            "sw_version": firmware_version,
            "serial_number": serial_number,
        }
        
    @property
    def device_info(self):
        """Return device information about this entity."""
        return self._device_info

    async def _UpdatePollingrate(self,pollingRate):
        self.update_interval = pollingRate

    async def _send_command(self, command):
        # Disable SSL warnings
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
        """Send a command to the device."""
        url = f'https://{self.address}/httpapi.asp'
        payload = f'command=sendAppController&payload={{"key_pressed": "{command}"}}'
        async with aiohttp.ClientSession() as session:
            with async_timeout.timeout(10):
                async with session.post(url, data=payload,  ssl=self.sslcontext) as response:
                    if response.status != 200:
                        _LOGGER.error("Failed to send command: %s", response.status)

    async def _async_update_data(self):
        data1 = await self.requestInfo()
        data2 = await self.getEQ()
        combined_data = self.merge_two_dicts(data1, data2)
        
        # Ensure self.data is initialized to an empty dictionary if it is None
        if self.data is None:
            self.data = {}
        
        self.data.update(combined_data)
        return combined_data

    async def getDeviceInfo(self):
        # Disable SSL warnings
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
        url = f'https://{self.address}/httpapi.asp?command=getDeviceInfo'
        headers = {
        'Accept-Encoding': "gzip",
        }
        
        async with aiohttp.ClientSession() as session:
            try:
                with async_timeout.timeout(10):
                    async with session.get(url, headers=headers,  ssl=self.sslcontext) as response:
                        if response.status == 200:
                            response_text = await response.text()
                            response_json = json.loads(response_text)
                            #_LOGGER.debug("Device Info Response text: %s", response_text)
                            #get data out of JSON
                            device_info = response_json["device_info"]
                            return device_info
                        else:
                            _LOGGER.error("Failed to get device info: %s", response.status)
                            return {}

            except Exception as e:
                _LOGGER.error("Error getting device info: %s", str(e))
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
                            _LOGGER.error("Failed to fetch data: %s", response.status)
                            return {}
        except Exception as e:
            _LOGGER.error("Error fetching data: %s", str(e))
            raise ConfigEntryNotReady(f"Timeout while connecting to {self.address}")
            return {}
            

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
                with async_timeout.timeout(10):
                    async with session.post(url, headers=headers, data=payload) as response:
                        if response.status == 200:
                            response_text = await response.text()
                            _LOGGER.debug("Response text: %s", response_text)
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
                                _LOGGER.error("Could not find necessary data in the response")
                                return {}
                        else:
                            _LOGGER.error("Failed to fetch data: %s", response.status)
                            return {}
            except Exception as e:
                _LOGGER.error("Error fetching data: %s", str(e))
                return {}

    async def setVolume(self, value: float):
        """Fetch data from the API."""
        url = f'http://{self._entry.data["ip_address"]}:59152/upnp/control/rendercontrol1'
        headers = {
            "Content-type": 'text/xml;charset="utf-8"',
            'Soapaction': "\"urn:schemas-upnp-org:service:RenderingControl:1#SetVolume\""
        }
        payload = "<?xml version=\"1.0\" encoding=\"utf-8\" standalone=\"yes\"?><s:Envelope s:encodingStyle=\"http://schemas.xmlsoap.org/soap/encoding/\" xmlns:s=\"http://schemas.xmlsoap.org/soap/envelope/\"><s:Body><u:SetVolume xmlns:u=\"urn:schemas-upnp-org:service:RenderingControl:1\"><InstanceID>0</InstanceID><Channel>Single</Channel><DesiredVolume>DesiredVolumeNumber</DesiredVolume></u:SetVolume></s:Body></s:Envelope>"
        payload = payload.replace("DesiredVolumeNumber", str(round(value)) )
        
        async with aiohttp.ClientSession() as session:
            try:
                with async_timeout.timeout(10):
                    async with session.post(url, headers=headers, data=payload) as response:
                        if response.status != 200:
                            _LOGGER.error("Failed to set volume: %s", response.status)
                            return {}
            except Exception as e:
                _LOGGER.error("Error setting volume: %s", str(e))
                return {}

    async def getEQ(self):
        # Disable SSL warnings
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
        url = f'https://{self.address}/httpapi.asp?command=getEQ'
        headers = {
        'Accept-Encoding': "gzip",
        }
        async with aiohttp.ClientSession() as session:
            try:
                with async_timeout.timeout(10):
                    async with session.get(url, headers=headers,  ssl=self.sslcontext) as response:
                        if response.status == 200:
                            response_text = await response.text()
                            response_json = json.loads(response_text)
                            _LOGGER.debug("EQ Response text: %s", response_text)
                            #get data out of JSON
                            gain = response_json["eq_setting"]["eq_payload"]["gain"]
                            gatheredData = {
                                "EQ_1_Low": gain[0],
                                "EQ_2_Mid": gain[1],
                                "EQ_3_High": gain[2]
                            }
                            return gatheredData
                        else:
                            _LOGGER.error("Failed to get EQ: %s", response.status)
                            return {}
            except Exception as e:
                _LOGGER.warning("Error getting EQ: %s", str(e))
                return {}

    async def setEQ(self, value: float, frequency):
        # Disable SSL warnings
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        """Fetch data from the API."""
        url = f'https://{self._entry.data["ip_address"]}/httpapi.asp'
        headers = {
        'Accept-Encoding': "gzip",
        }
        payload = "command=setEQ&payload={\"eq_id\":\"1\",\"eq_name\":\"Custom\",\"eq_payload\":{\"fs\":[150.0,1000.0,6000.0],\"gain\":[BassFrequency,MidFrequency,HighFrequency],\"q\":[0.7070000171661377,0.5,0.7070000171661377],\"type\":[17.0,11.0,16.0]},\"eq_status\":\"on\"}"
        BassFrequency = str(self.data.get("EQ_1_Low")) if "EQ_1_Low"!= frequency else str(round(value,1))
        MidFrequency = str(self.data.get("EQ_2_Mid")) if "EQ_2_Mid"!= frequency else str(round(value,1))
        HighFrequency = str(self.data.get("EQ_3_High")) if "EQ_3_High"!= frequency else str(round(value,1))
        payload = payload.replace("BassFrequency",BassFrequency).replace("MidFrequency",MidFrequency).replace("HighFrequency",HighFrequency)
        
        async with aiohttp.ClientSession() as session:
            try:
                with async_timeout.timeout(10):
                    async with session.post(url, headers=headers, data=payload,  ssl=self.sslcontext) as response:
                        if response.status != 200:
                            _LOGGER.error("Failed to set EQ: %s", response.status)
                            return {}
            except Exception as e:
                _LOGGER.error("Error setting EQ: %s", str(e))
                return {}

    def merge_two_dicts(self,x, y):
        z = x.copy()   # start with keys and values of x
        z.update(y)    # modifies z with keys and values of y
        return z