from __future__ import annotations

import logging
import re  # For IP address validation

import voluptuous as vol
from awesomeversion import AwesomeVersion

from homeassistant import config_entries
from homeassistant.config_entries import ConfigFlowResult, OptionsFlowWithReload
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_PORT, CONF_UUID, CONF_ADDRESS, CONF_SCAN_INTERVAL
from homeassistant.const import __version__ as HAVERSION
from homeassistant.helpers.service_info.zeroconf import ZeroconfServiceInfo
from homeassistant.core import callback

from .const import DOMAIN
from .coordinator import Coordinator

_LOGGER = logging.getLogger(__name__)

class JBLConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for JBL Integration."""
    VERSION = 2
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL

    def __init__(self) -> None:
        """Initialize the config flow."""
        _LOGGER.info("Initialize JBL Integration")
        self._discovered_devices = {}

    async def async_step_user(self, user_input=None):
        """Handle manual user setup."""
        errors = {}

        if user_input is not None:
            ip_address = user_input.get(CONF_ADDRESS)
            polling_rate = user_input.get(CONF_SCAN_INTERVAL)

            # Validate IP address format
            ip_pattern = re.compile(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$")
            if not ip_pattern.match(ip_address):
                errors[CONF_ADDRESS] = "invalid_ip"

            # Validate polling rate range
            if not (1 <= polling_rate <= 3600):
                errors[CONF_SCAN_INTERVAL] = "invalid_polling_rate"

            if not errors:
                coordinator = Coordinator(ip_address, polling_rate)
                try:
                    device_Type = await coordinator.getDeviceType()
                    if device_Type.get("hm_product_name", "unknown_product") == "unknown_product":
                        errors[CONF_SCAN_INTERVAL] = "could not reach device"
                except Exception:
                    errors[CONF_SCAN_INTERVAL] = "could not reach device"

            # If no errors, create the entry
            if not errors:
                return self.async_create_entry(
                    title=device_Type.get("hm_product_name", "unknown_product"),
                    data=user_input
                )

        # Show the form again if errors or no input yet
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_ADDRESS, description={"suggested_value": "192.148.4.66"}): str,
                vol.Required(CONF_SCAN_INTERVAL, description={"suggested_value": 5}): int,
            }),
            errors=errors,
        )

    async def async_step_zeroconf(self, discovery_info: ZeroconfServiceInfo) -> ConfigFlowResult:
        """Handle zeroconf discovery."""
        _LOGGER.debug("Discovered JBL device: %s", discovery_info)

        # Extract device info from zeroconf
        self.host = discovery_info.host
        self.port = discovery_info.port
        self.name = (
            discovery_info.name.removesuffix("_jbl-product._tcp.local.")
            if discovery_info.name else "JBL Device"
        )
        self._unique_id = discovery_info.properties.get("uuid", "").replace("uuid:", "")
        existing_config_entry = await self.async_set_unique_id(self._unique_id)

        self.address = self.host
        properties = dict(discovery_info.properties) if discovery_info.properties else {}

        configuration = {
            CONF_HOST: self.host,
            CONF_PORT: self.port,
            CONF_NAME: self.name,
            CONF_UUID: self._unique_id,
            CONF_ADDRESS: self.address,
            "properties": properties
        }

        self._discovered_devices[self._unique_id] = configuration

        # Handle multiple IP addresses from zeroconf
        if (
            existing_config_entry
            and CONF_HOST in existing_config_entry.data
            and len(discovery_info.ip_addresses) > 1
        ):
            existing_host = existing_config_entry.data[CONF_HOST]
            if existing_host != self.host:
                if existing_host in [str(ip_address) for ip_address in discovery_info.ip_addresses]:
                    self.host = existing_host

        # If no UUID, check if the IP address matches an existing device
        for entry in self._async_current_entries():
            if entry.data.get(CONF_ADDRESS) == self.address:
                # Update the existing entry with new data
                self.hass.config_entries.async_update_entry(
                    entry,
                    data={**entry.data, **configuration},
                )
                _LOGGER.debug("Updated existing JBL device with IP address: %s", self.address)
                return self.async_abort(reason="already_configured")



        # Abort if already configured
        self._abort_if_unique_id_configured(
            updates=configuration
        )
        _LOGGER.debug("New JBL TV device found via zeroconf: %s", self.name)
        self.context.update({"title_placeholders": {CONF_NAME: self.name}})
        return await self.async_step_zeroconf_confirm()

    async def async_step_zeroconf_confirm(self, user_input=None) -> ConfigFlowResult:
        """Confirm zeroconf discovery before adding."""
        errors = {}
        unique_id = self._unique_id
        device_info = self._discovered_devices.get(unique_id, {})
        ip_address = device_info.get(CONF_ADDRESS, 'error')
        polling_rate = 5
        
         # If IP address extraction failed, show error
        if ip_address == 'error':
            errors[CONF_ADDRESS] = "Could not extract IP address"
            _LOGGER.info("JBL Integration - Device discovery: Could not extract IP address")
        
        # if not errors and user_input is None:
        #     coordinator = Coordinator(ip_address, polling_rate)
        #     try:
        #         device_Type = await coordinator.getDeviceType()
        #         if device_Type.get("hm_product_name", "unknown_product") == "unknown_product":
        #             errors["ip_address"] = "could not reach device"
        #     except Exception:
        #         errors["ip_address"] = "could not reach device"
        
        # if not errors and user_input is None:
        #     dataFromDiscovery = {
        #         "ip_address": ip_address,
        #         "polling_rate": polling_rate
        #     }
            
        #     return self.async_create_entry(
        #         title=device_Type.get("hm_product_name", "unknown_product"),
        #         data=dataFromDiscovery
        #     )
            
        

        # If user submitted the form, validate input
        if user_input is not None:
            ip_address = user_input.get(CONF_ADDRESS)
            polling_rate = user_input.get(CONF_SCAN_INTERVAL)

            # Validate IP address format
            ip_pattern = re.compile(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$")
            if not ip_pattern.match(ip_address):
                errors[CONF_ADDRESS] = "invalid_ip"

            # Validate polling rate range
            if not (1 <= polling_rate <= 3600):
                errors[CONF_SCAN_INTERVAL] = "invalid_polling_rate"

            if not errors:
                coordinator = Coordinator(ip_address, polling_rate)
                try:
                    device_Type = await coordinator.getDeviceType()
                    if device_Type.get("hm_product_name", "unknown_product") == "unknown_product":
                        errors[CONF_ADDRESS] = "could not reach device"
                except Exception:
                    errors[CONF_ADDRESS] = "could not reach device"
            
            if not errors:
                device_info[CONF_ADDRESS] = ip_address
                device_info[CONF_SCAN_INTERVAL] = polling_rate
                
            # If no errors, create the entry
            if not errors:
                return self.async_create_entry(
                    title=device_Type.get("hm_product_name", "unknown_product"),
                    data=device_info
                )

                

        # Show confirmation form with description from strings.json
        return self.async_show_form(
            step_id="zeroconf_confirm",
            data_schema=vol.Schema({
                vol.Required(CONF_ADDRESS, description={"suggested_value": ip_address}): str,
                vol.Required(CONF_SCAN_INTERVAL, description={"suggested_value": polling_rate}): int,
            }),
            errors=errors,
            description_placeholders={"name": device_info.get(CONF_NAME, "JBL Device")},
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Return the options flow handler."""
        return OptionsFlowHandler(config_entry)


OPTIONS_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_ADDRESS): str,
        vol.Required(CONF_SCAN_INTERVAL): int,
    }
)

class OptionsFlowHandler(OptionsFlowWithReload):
    
    def __init__(self, config_entry):
        if AwesomeVersion(HAVERSION) < "2024.11.99":
            self.config_entry = config_entry

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Manage the options."""
        return await self.async_step_user()

    async def async_step_user(self, user_input=None) -> ConfigFlowResult:
        
        if user_input is not None:
            newData = {}
            newData.update(self.config_entry.data)
            newData.update(user_input)
            _LOGGER.debug("JBL entry updated: "+str(newData))
            self.hass.config_entries.async_update_entry(self.config_entry, data=newData)
            result = self.async_create_entry(data=newData)
            await self.hass.config_entries.async_reload(self.config_entry.entry_id)
            return result
        
        schema = {
            vol.Optional(CONF_ADDRESS, default=self.config_entry.data.get(CONF_ADDRESS, 5),): str,
            vol.Optional(CONF_SCAN_INTERVAL, default=self.config_entry.data.get(CONF_SCAN_INTERVAL, 5),): int,
        }


        return self.async_show_form(step_id="user", data_schema=vol.Schema(schema))
