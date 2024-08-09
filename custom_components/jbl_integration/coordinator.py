"""Sensor platform for JBL integration."""
import aiohttp
import async_timeout
import json
import logging
from datetime import timedelta
from homeassistant.helpers.entity import Entity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

class Coordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the API."""

    def __init__(self, hass, entry, address, pollingRate):
        """Initialize the coordinator."""
        self._entry = entry
        self.address = address
        self.pollingRate = pollingRate
        self.data = {}
        super().__init__(
            hass,
            _LOGGER,
            name="JBL Sensor",
            update_method=self._async_update_data,
            update_interval=timedelta(seconds=pollingRate),
        ) 

    async def _SetupDeviceInfo(self):
        device_info = await self.getDeviceInfo()
            
        # Ensure device_info has all the expected keys and provide fallback values if necessary
        mac_address = device_info.get("wlan0_mac", "unknown_mac")
        uuid = device_info.get("uuid", "unknown_uuid")
        device_name = device_info.get("name", "JBL Bar 800")
        serial_number = device_info.get("serial_number", "unknown_serial")
        firmware_version = device_info.get("firmware", "unknown_firmware")
        
        self._device_info = {
            "identifiers": {(DOMAIN, self._entry.entry_id, mac_address, uuid, str(uuid).replace("-", "") , self.address)},
            "name": device_name,
            "manufacturer": "HARMAN International Industries",
            "model": "JBL Bar 800",
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
        """Send a command to the device."""
        url = f'http://{self.address}/httpapi.asp'
        payload = f'command=sendAppController&payload={{"key_pressed": "{command}"}}'
        async with aiohttp.ClientSession() as session:
            with async_timeout.timeout(10):
                async with session.post(url, data=payload) as response:
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
        url = f'http://{self.address}/httpapi.asp?command=getDeviceInfo'
        headers = {
        'Accept-Encoding': "gzip",
        }
        async with aiohttp.ClientSession() as session:
            try:
                with async_timeout.timeout(10):
                    async with session.get(url, headers=headers) as response:
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
        url = f'http://{self.address}:59152/upnp/control/rendercontrol1'
        headers = {
            "Content-type": 'text/xml;charset="utf-8"',
            "Soapaction": '"urn:schemas-upnp-org:service:AVTransport:1#GetInfoEx"'
        }
        payload = """
        <?xml version="1.0" encoding="utf-8" standalone="yes"?>
        <s:Envelope s:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/" xmlns:s="http://schemas.xmlsoap.org/soap/envelope/">
          <s:Body>
            <u:GetInfoEx xmlns:u="urn:schemas-upnp-org:service:RenderingControl:1">
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
                            #_LOGGER.debug("Response text: %s", response_text)
                            # Parse the XML response manually, as it's not JSON
                            from xml.etree import ElementTree as ET
                            root = ET.fromstring(response_text)
                            namespaces = {
                                's': 'http://schemas.xmlsoap.org/soap/envelope/',
                                'u': 'urn:schemas-upnp-org:service:RenderingControl:1'
                            }
                            try:
                                status = root.find('.//u:GetInfoExResponse/Status', namespaces).text
                                deviceType = status.get("hm_product_name", "unknown_product")
                                return deviceType
                            except AttributeError:
                                _LOGGER.error("Could not find necessary device type in the response")
                                return {}
                        else:
                            _LOGGER.error("Failed to fetch data: %s", response.status)
                            return {}
            except Exception as e:
                _LOGGER.error("Error fetching data: %s", str(e))
                return {}

    async def requestInfo(self):
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
        url = f'http://{self.address}/httpapi.asp?command=getEQ'
        headers = {
        'Accept-Encoding': "gzip",
        }
        async with aiohttp.ClientSession() as session:
            try:
                with async_timeout.timeout(10):
                    async with session.get(url, headers=headers) as response:
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
                _LOGGER.error("Error getting EQ: %s", str(e))
                return {}

    async def setEQ(self, value: float, frequency):
        """Fetch data from the API."""
        url = f'http://{self._entry.data["ip_address"]}/httpapi.asp'
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
                    async with session.post(url, headers=headers, data=payload) as response:
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