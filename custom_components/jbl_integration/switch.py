"""Switch platform for JBL integration."""
import async_timeout
import logging
from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.event import async_track_state_change

from .const import DOMAIN
from .coordinator import Coordinator

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    """Set up the JBL switch platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]

    async_add_entities([
        JBLPowerSwitch(entry, coordinator),
        #add more switches
    ])


class JBLPowerSwitch(SwitchEntity):
    """Representation of a switch to control JBL power."""

    def __init__(self, entry: ConfigEntry, coordinator: Coordinator):
        """Initialize the switch."""
        self._entry = entry
        self._is_on = False
        self.coordinator = coordinator        
        self.entity_id = f"switch.{self.coordinator.device_info.get("name", "jbl_integration").replace(' ', '_').lower()}_power"

    @property
    def name(self):
        """Return the name of the switch."""
        return "JBL Power"

    @property
    def unique_id(self):
        """Return a unique ID for the switch."""
        return f"jbl_power_{self._entry.entry_id}"

    @property
    def is_on(self):
        """Return true if switch is on."""
        return self.coordinator.data.get("play_medium") != "UNKNOWN"

    @property
    def device_info(self):
        """Return device information about this entity."""
        return self.coordinator.device_info


    async def async_turn_on(self, **kwargs):
        """Turn the switch on."""
        #Toggle Switch Fast
        #self._is_on = True
        #self.async_write_ha_state()
        #Actual update
        await self.coordinator._send_command("power")
        await self.coordinator.async_request_refresh()
        #self._is_on =  self.coordinator.data.get("play_medium") != "UNKNOWN"
        #self.async_write_ha_state()



    async def async_turn_off(self, **kwargs):
        """Turn the switch off."""
        #Toggle Switch Fast
        #self._is_on = False
        #self.async_write_ha_state()
        #Actual update
        await self.coordinator._send_command("power")
        await self.coordinator.async_request_refresh()
        #self._is_on =  self.coordinator.data.get("play_medium") != "UNKNOWN"
        #self.async_write_ha_state()

    @property
    def should_poll(self):
        """No polling needed."""
        return False

    async def async_added_to_hass(self):
        """When entity is added to hass."""
        self.async_on_remove(self.coordinator.async_add_listener(self.async_write_ha_state))

    async def async_update(self):
        """Update the sensor."""
        await self.coordinator.async_request_refresh()
