
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
import re  # For IP address validation
from .const import DOMAIN
from .coordinator import Coordinator

class JBLConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL

    async def async_step_user(self, user_input=None):
        errors = {}

        if user_input is not None:
            ip_address = user_input.get("ip_address")
            polling_rate = user_input.get("polling_rate")

            # Simple validation for IP address format (you can make it more strict)
            ip_pattern = re.compile(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$")
            if not ip_pattern.match(ip_address):
                errors["ip_address"] = "invalid_ip"

            # Validate that polling rate is between 1 and 10
            if not (1 <= polling_rate <= 3600):
                errors["polling_rate"] = "invalid_polling_rate"

            if not errors:
                coordinator = Coordinator(ip_address, polling_rate)
                try:
                    device_Type = await coordinator.getDeviceType() 
                    if device_Type.get("hm_product_name", "unknown_product") == "unknown_product":
                        errors["ip_address"] = "could not reach device"
                except Exception as e:
                    errors["ip_address"] = "could not reach device"


            # If no errors, create the entry
            if not errors:
                return self.async_create_entry(title=device_Type.get("hm_product_name", "unknown_product"), data=user_input)

        # If there are errors or no input yet, show the form again
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required("ip_address", description={"suggested_value": "192.148.4.66"}): str,
                    vol.Required("polling_rate", description={"suggested_value": 5}): int,
                }
            ),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return OptionsFlowHandler(config_entry)

class OptionsFlowHandler(config_entries.OptionsFlow):
    def __init__(self, config_entry):
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        "polling_rate",
                        default=self.config_entry.options.get("polling_rate", 5),
                    ): int,
                }
            ),
        )
