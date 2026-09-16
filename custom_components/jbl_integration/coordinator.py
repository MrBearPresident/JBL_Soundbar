"""Sensor platform for JBL integration."""
import asyncio
import aiohttp
import json
import logging
import urllib3
import ssl
import certifi
import html
import socket
from datetime import timedelta
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_PORT, CONF_UUID, CONF_ADDRESS, CONF_SCAN_INTERVAL
from homeassistant.exceptions import ConfigEntryNotReady
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

class Coordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the API."""

    def __init__(self, address, scan_interval, hass=None, entry=None):
        """Initialize the coordinator."""
        self.address = address
        self.pollingRate = scan_interval
        self.data = {}
        self._rendering_control_sid = None
        self._rendering_control_renew_task = None

        ssl_context = ssl.create_default_context(cafile=certifi.where())
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        self.sslcontext = ssl_context
    
        if hass != None and entry != None:
            self._entry = entry
            self.hass = hass
            super().__init__(
                hass,
                _LOGGER,
                name="JBL Sensor",
                update_method=self._async_update_data,
                update_interval=timedelta(seconds=int(scan_interval)),
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
        try:
            self._newFirmware = int(firmware_version.split('.')[0])>24 or int(firmware_version.split('.')[2])>31
            _LOGGER.debug("JBL one 3.0 Detected" if self._newFirmware else "Older firmware then JBL one 3.0")
        except Exception as e:
            self._newFirmware = False
            
    @property
    def device_info(self):
        """Return device information about this entity."""
        return self._device_info
    
    @property
    def newFirmware(self):
        """Return if the JBL is part of the JBL one 3.0 software"""
        return self._newFirmware

    async def _UpdatePollingrate(self,pollingRate):
        self.update_interval = pollingRate

    async def _send_command(self, command):
        # Disable SSL warnings
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
        """Send a command to the device."""
        url = f'https://{self.address}/httpapi.asp'
        payload = f'command=sendAppController&payload={{"key_pressed": "{command}"}}'
        async with aiohttp.ClientSession() as session:
            async with asyncio.timeout(10):
                async with session.post(url, data=payload,  ssl=self.sslcontext) as response:
                    if response.status != 200:
                        _LOGGER.error("Failed to send command: %s", response.status)

    async def _async_update_data(self):
        combined_data = {
            **await self.requestInfo(),
            **await self.getEQ(),
            **await self.getEQPresets(),
            **await self.getNightMode(),
            **await self.getRearSpeaker(),
            **await self.getSmartMode(),
            **await self.getPureVoice(),
        }

        # Ensure self.data is initialized to an empty dictionary if it is None
        if self.data is None:
            self.data = {}

        if "audio_format" in self.data:
            combined_data["audio_format"] = self.data["audio_format"]
        if "tv_stream_info" in self.data:
            combined_data["tv_stream_info"] = self.data["tv_stream_info"]
        
        self.data.update(combined_data)
        return self.data

    async def _getCommand(self, command):
        # Disable SSL warnings
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
        url = f'https://{self.address}/httpapi.asp?command={command}'
        
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
                            _LOGGER.debug(f"%s Response text: %s", command, response_text)
                            return response_json
                        else:
                            _LOGGER.error(f"Failed to get %s: %s", command, response.status)
                            return {}
            except Exception as e:
                _LOGGER.error(f"Error getting %s: %s", command, str(e))
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
            raise ConfigEntryNotReady(f"Timeout while connecting to {self.address}") from e
            
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
        url = f'http://{self._entry.data[CONF_ADDRESS]}:59152/upnp/control/rendercontrol1'
        headers = {
            "Content-type": 'text/xml;charset="utf-8"',
            'Soapaction': "\"urn:schemas-upnp-org:service:RenderingControl:1#SetVolume\""
        }
        payload = "<?xml version=\"1.0\" encoding=\"utf-8\" standalone=\"yes\"?><s:Envelope s:encodingStyle=\"http://schemas.xmlsoap.org/soap/encoding/\" xmlns:s=\"http://schemas.xmlsoap.org/soap/envelope/\"><s:Body><u:SetVolume xmlns:u=\"urn:schemas-upnp-org:service:RenderingControl:1\"><InstanceID>0</InstanceID><Channel>Single</Channel><DesiredVolume>DesiredVolumeNumber</DesiredVolume></u:SetVolume></s:Body></s:Envelope>"
        payload = payload.replace("DesiredVolumeNumber", str(round(value)) )
        
        async with aiohttp.ClientSession() as session:
            try:
                async with asyncio.timeout(10):
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
        
        if self.newFirmware: 
            url = f'https://{self.address}/httpapi.asp?command=getEQList' 
        else:
            url = f'https://{self.address}/httpapi.asp?command=getEQ' 
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
                            _LOGGER.debug("EQ Response text: %s", response_text)
                            #get data out of JSON
                            if self.newFirmware:
                                active_id = str(response_json.get("active_eq_id", "0"))
                                active_preset = None
                                for item in response_json.get("eq_list", []):
                                    if str(item.get("eq_id", "")) == active_id:
                                        active_preset = item
                                        break
                                if active_preset is None and response_json.get("eq_list"):
                                    active_preset = response_json["eq_list"][0]
                                if active_preset is None:
                                    return {}
                                gain = active_preset["eq_payload"]["gain"]
                                eqList = {
                                        "125Hz":gain[0],    #Min -9, Max 6, step 0.5
                                        "250Hz":gain[1],    #Min -6, Max 6, step 0.5
                                        "500Hz":gain[2],    #Min -6, Max 6, step 0.5
                                        "1000Hz":gain[3],   #Min -6, Max 6, step 0.5
                                        "2000Hz":gain[4],   #Min -6, Max 6, step 0.5
                                        "4000Hz":gain[5],   #Min -6, Max 6, step 0.5
                                        "8000Hz":gain[6],   #Min -6, Max 6, step 0.5
                                    }
                                return eqList
                            else:
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
        url = f'https://{self._entry.data[CONF_ADDRESS]}/httpapi.asp'
        headers = {
        'Accept-Encoding': "gzip",
        }
        if self.newFirmware:
            eqList = {
                        "125Hz":self.data.get("125Hz",0),  #Min -9, Max 6, step 0.5
                        "250Hz":self.data.get("250Hz",0),  #Min -6, Max 6, step 0.5
                        "500Hz":self.data.get("500Hz",0),  #Min -6, Max 6, step 0.5
                        "1000Hz":self.data.get("1000Hz",0), #Min -6, Max 6, step 0.5
                        "2000Hz":self.data.get("2000Hz",0), #Min -6, Max 6, step 0.5
                        "4000Hz":self.data.get("4000Hz",0), #Min -6, Max 6, step 0.5
                        "8000Hz":self.data.get("8000Hz",0), #Min -6, Max 6, step 0.5
                    }
            eqList[frequency] = value
            payload = "command=setActiveEQ&payload={\"active_eq_id\":\"0\",\"band\":7,\"eq_payload\":{\"fs\":[125.0,250.0,500.0,1000.0,2000.0,4000.0,8000.0],\"gain\":[125Hz,250Hz,500Hz,1000Hz,2000Hz,4000Hz,8000Hz]}}"

            for key in eqList.keys():
                payload = payload.replace(key,str(eqList.get(key))) 
        else:
            payload = "command=setEQ&payload={\"eq_id\":\"1\",\"eq_name\":\"Custom\",\"eq_payload\":{\"fs\":[150.0,1000.0,6000.0],\"gain\":[BassFrequency,MidFrequency,HighFrequency],\"q\":[0.7070000171661377,0.5,0.7070000171661377],\"type\":[17.0,11.0,16.0]},\"eq_status\":\"on\"}"
            BassFrequency = str(self.data.get("EQ_1_Low")) if "EQ_1_Low"!= frequency else str(round(value,1))
            MidFrequency = str(self.data.get("EQ_2_Mid")) if "EQ_2_Mid"!= frequency else str(round(value,1))
            HighFrequency = str(self.data.get("EQ_3_High")) if "EQ_3_High"!= frequency else str(round(value,1))
            payload = payload.replace("BassFrequency",BassFrequency).replace("MidFrequency",MidFrequency).replace("HighFrequency",HighFrequency)
        
        async with aiohttp.ClientSession() as session:
            try:
                async with asyncio.timeout(10):
                    async with session.post(url, headers=headers, data=payload,  ssl=self.sslcontext) as response:
                        if response.status != 200:
                            _LOGGER.error("Failed to set EQ: %s", response.status)
                            return {}
                        else:
                            return {}
            except Exception as e:
                _LOGGER.error("Error setting EQ: %s", str(e))
                return {}

    async def getNightMode(self):
        response = await self._getCommand("getPersonalListeningMode")
        if "status" in response:
            return { "NightMode": response["status"] }
        else:
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
                            _LOGGER.error("Failed to set Nightmode: %s", response.status)
                            return {}
                        else:
                            return {}
            except Exception as e:
                _LOGGER.error("Error setting Nightmode: %s", str(e))
                return {}

    async def getRearSpeaker(self):
        response = await self._getCommand("getRearSpeakerStatus")
        if "rears" in response:
            return { "Rears": response["rears"] }
        else:
            return {}
    
    async def getSmartMode(self):
        response = await self._getCommand("getSmartMode")
        if "status" in response:
            return { "SmartMode": response["status"] }
        else:
            return {}

    async def getPureVoice(self):
        response = await self._getCommand("getPureVoiceState")
        if "purevoice_state" in response:
            return { "PureVoice": "on" if response["purevoice_state"] == "1" else "off" }
        else:
            return {}

    async def async_start_rendering_control_events(self):
        """Subscribe to RenderingControl GENA events for HarmanBarState updates."""
        if self._rendering_control_sid:
            return

        callback_url = self._rendering_control_callback_url()
        url = f"http://{self.address}:49152/upnp/event/rendercontrol1"
        headers = {
            "CALLBACK": f"<{callback_url}>",
            "NT": "upnp:event",
            "TIMEOUT": "Second-300",
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with asyncio.timeout(10):
                    async with session.request("SUBSCRIBE", url, headers=headers) as response:
                        if response.status not in (200, 202):
                            response_text = await response.text()
                            _LOGGER.warning(
                                "Failed to subscribe RenderingControl events: %s %s",
                                response.status,
                                response_text,
                            )
                            return

                        self._rendering_control_sid = response.headers.get("SID")
                        if self._rendering_control_sid and self._rendering_control_renew_task is None:
                            self._rendering_control_renew_task = self.hass.async_create_task(
                                self._async_renew_rendering_control_events()
                            )
                        _LOGGER.debug(
                            "Subscribed RenderingControl events for %s: %s via %s",
                            self.address,
                            self._rendering_control_sid,
                            callback_url,
                        )
        except Exception as e:
            _LOGGER.warning("Error subscribing RenderingControl events: %s", str(e))

    async def async_stop_rendering_control_events(self):
        """Unsubscribe from RenderingControl GENA events."""
        if self._rendering_control_renew_task is not None:
            self._rendering_control_renew_task.cancel()
            self._rendering_control_renew_task = None

        if not self._rendering_control_sid:
            return

        url = f"http://{self.address}:49152/upnp/event/rendercontrol1"
        headers = {"SID": self._rendering_control_sid}
        self._rendering_control_sid = None

        try:
            async with aiohttp.ClientSession() as session:
                async with asyncio.timeout(5):
                    await session.request("UNSUBSCRIBE", url, headers=headers)
        except Exception as e:
            _LOGGER.debug("Error unsubscribing RenderingControl events: %s", str(e))

    async def _async_renew_rendering_control_events(self):
        """Renew RenderingControl GENA subscription before it expires."""
        url = f"http://{self.address}:49152/upnp/event/rendercontrol1"

        while self._rendering_control_sid:
            await asyncio.sleep(240)
            if not self._rendering_control_sid:
                return

            headers = {
                "SID": self._rendering_control_sid,
                "TIMEOUT": "Second-300",
            }
            try:
                async with aiohttp.ClientSession() as session:
                    async with asyncio.timeout(10):
                        async with session.request("SUBSCRIBE", url, headers=headers) as response:
                            if response.status not in (200, 202):
                                _LOGGER.warning(
                                    "Failed to renew RenderingControl events: %s",
                                    response.status,
                                )
            except asyncio.CancelledError:
                raise
            except Exception as e:
                _LOGGER.debug("Error renewing RenderingControl events: %s", str(e))

    async def async_handle_rendering_control_notify(self, body):
        """Handle RenderingControl NOTIFY body and update audio format."""
        try:
            stream_info = self._extract_tv_stream_info(body)
        except Exception as e:
            _LOGGER.debug("Error parsing RenderingControl event: %s", str(e))
            return False

        if stream_info is None:
            return False

        audio_format = self._format_tv_stream_info(stream_info)
        if audio_format is None:
            return False

        self.data["audio_format"] = audio_format
        self.data["tv_stream_info"] = stream_info
        self.async_set_updated_data(self.data)
        return True

    def _rendering_control_callback_url(self):
        callback_host = self._callback_host()
        callback_port = getattr(self.hass.http, "server_port", None) or 8123
        return f"http://{callback_host}:{callback_port}/api/{DOMAIN}/{self._entry.entry_id}/rendering_control"

    def _callback_host(self):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
                sock.connect((self.address, 59152))
                return sock.getsockname()[0]
        except OSError:
            return self.address

    def _extract_tv_stream_info(self, response_text):
        candidates = [response_text]

        try:
            from xml.etree import ElementTree as ET

            root = ET.fromstring(response_text)
            for element in root.iter():
                if element.text and "HarmanBarState" in element.text:
                    candidates.append(element.text)
                    unescaped_text = html.unescape(element.text)
                    if unescaped_text != element.text:
                        candidates.append(unescaped_text)
        except Exception as e:
            _LOGGER.debug("Could not parse audio format response wrapper: %s", str(e))

        for candidate in candidates:
            try:
                root = ET.fromstring(candidate)
            except Exception as e:
                _LOGGER.debug("Could not parse TV stream info XML: %s", str(e))
                continue

            for element in root.iter():
                if element.tag.split("}")[-1] != "HarmanBarState":
                    continue

                harman_state = element.attrib.get("val")
                if not harman_state:
                    continue

                state = json.loads(html.unescape(harman_state))
                stream_info = state.get("tv_stream_info")
                if isinstance(stream_info, dict):
                    return stream_info

        return None

    def _format_tv_stream_info(self, stream_info):
        codec_type = stream_info.get("codec_type")
        proc_type = stream_info.get("proc_type")
        channels = stream_info.get("channels")
        sample_rate = stream_info.get("sample_rate")

        parts = []
        if proc_type:
            parts.append(str(proc_type))

        if codec_type and codec_type != proc_type:
            parts.append(str(codec_type))

        if channels:
            parts.append(f"{channels}ch")

        if sample_rate:
            try:
                parts.append(f"{int(sample_rate) / 1000:g} kHz")
            except (TypeError, ValueError):
                parts.append(f"{sample_rate} Hz")

        if parts:
            return " / ".join(parts)
        return None
            
    async def setPureVoice(self, value: bool):
        # Disable SSL warnings
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        """Fetch data from the API."""
        url = f'https://{self.address}/httpapi.asp'
        headers = {
        'Accept-Encoding': "gzip",
        }
        
        strvalue = '1' if value else '0'
        payload = 'command=setPureVoiceState&payload={"purevoice_state":"'+strvalue+'"}'

        async with aiohttp.ClientSession() as session:
            try:
                async with asyncio.timeout(10):
                    async with session.post(url, headers=headers, data=payload,  ssl=self.sslcontext) as response:
                        if response.status != 200:
                            _LOGGER.error("Failed to set PureVoice: %s", response.status)
                            return {}
                        else:
                            return {}
            except Exception as e:
                _LOGGER.error("Error setting PureVoice: %s", str(e))
                return {}

    async def getEQPresets(self):
        """Fetch the list of EQ presets and the currently active one."""
        if not self.newFirmware:
            return {}

        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        url = f'https://{self.address}/httpapi.asp?command=getEQList'
        headers = {'Accept-Encoding': "gzip"}

        async with aiohttp.ClientSession() as session:
            try:
                async with asyncio.timeout(10):
                    async with session.get(url, headers=headers, ssl=self.sslcontext) as response:
                        if response.status == 200:
                            response_text = await response.text()
                            response_json = json.loads(response_text)
                            _LOGGER.debug("EQ Presets Response: %s", response_text)

                            eq_list = response_json.get("eq_list", [])
                            active_id = str(response_json.get("active_eq_id", "0"))

                            preset_map = {}
                            preset_data = {}
                            active_name = None
                            for item in eq_list:
                                eq_id = str(item.get("eq_id", ""))
                                eq_name = item.get("eq_name", f"Preset {eq_id}")
                                preset_map[eq_id] = eq_name
                                preset_data[eq_id] = item
                                if eq_id == active_id:
                                    active_name = eq_name

                            if not active_name and preset_map:
                                active_name = next(iter(preset_map.values()))

                            return {
                                "eq_preset_map": preset_map,
                                "eq_preset_data": preset_data,
                                "eq_active_preset": active_name,
                                "eq_active_id": active_id,
                            }
                        else:
                            _LOGGER.error("Failed to get EQ presets: %s", response.status)
                            return {}
            except Exception as e:
                _LOGGER.warning("Error getting EQ presets: %s", str(e))
                return {}

    async def setActiveEQPreset(self, eq_id: str):
        """Set the active EQ preset by its ID, sending full payload."""
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        preset_data = self.data.get("eq_preset_data", {})
        preset = preset_data.get(eq_id)
        if not preset:
            _LOGGER.error("EQ preset data not found for id: %s", eq_id)
            return

        send_payload = json.dumps({
            "active_eq_id": eq_id,
            "band": preset.get("band", 7),
            "eq_payload": preset.get("eq_payload", {}),
        })

        url = f'https://{self.address}/httpapi.asp'
        headers = {'Accept-Encoding': "gzip"}
        payload = f'command=setActiveEQ&payload={send_payload}'
        _LOGGER.debug("Setting EQ preset: %s", payload)

        async with aiohttp.ClientSession() as session:
            try:
                async with asyncio.timeout(10):
                    async with session.post(url, headers=headers, data=payload, ssl=self.sslcontext) as response:
                        if response.status != 200:
                            _LOGGER.error("Failed to set EQ preset: %s", response.status)
                        else:
                            _LOGGER.debug("EQ preset set successfully to id: %s", eq_id)
            except Exception as e:
                _LOGGER.error("Error setting EQ preset: %s", str(e))
