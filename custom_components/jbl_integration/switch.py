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

    entityArray = []
    entityArray.append(JBLPowerSwitch(entry, coordinator))
    if "SmartMode" in coordinator.data:
        entityArray.append(SmartModeSwitch(entry, coordinator))
    if "NightMode" in coordinator.data:
        entityArray.append(NightModeSwitch(entry, coordinator))
    if "PureVoice" in coordinator.data:
        entityArray.append(PureVoiceModeSwitch(entry, coordinator))    
    async_add_entities(entityArray)


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
    def icon(self):
        """Return the icon to use in the frontend."""
        return "mdi:power"
    
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

class NightModeSwitch(SwitchEntity):
    """Representation of a switch to control JBL NightMode."""

    def __init__(self, entry: ConfigEntry, coordinator: Coordinator):
        """Initialize the switch."""
        self._entry = entry
        self._is_on = False
        self.coordinator = coordinator        
        self.entity_id = f"switch.{self.coordinator.device_info.get("name", "jbl_integration").replace(' ', '_').lower()}_NightMode"

    @property
    def name(self):
        """Return the name of the switch."""
        return "JBL Night Mode"

    @property
    def unique_id(self):
        """Return a unique ID for the switch."""
        return f"jbl_night_mode_{self._entry.entry_id}"

    @property
    def is_on(self):
        """Return true if switch is on."""
        return self.coordinator.data.get("NightMode") == "on"

    @property
    def icon(self):
        """Return the icon to use in the frontend."""
        return"mdi:waveform"
    
    @property
    def device_info(self):
        """Return device information about this entity."""
        return self.coordinator.device_info

    async def async_turn_on(self, **kwargs):
        """Turn the switch on."""
        await self.coordinator.setNightMode(True)
        
    async def async_turn_off(self, **kwargs):
        """Turn the switch off."""
        await self.coordinator.setNightMode(False)

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

class SmartModeSwitch(SwitchEntity):
    """Representation of a switch to control JBL SmartMode."""

    def __init__(self, entry: ConfigEntry, coordinator: Coordinator):
        """Initialize the switch."""
        self._entry = entry
        self._is_on = False
        self.coordinator = coordinator        
        self.entity_id = f"switch.{self.coordinator.device_info.get('name', 'jbl_integration').replace(' ', '_').lower()}_smart_mode"

    @property
    def name(self):
        """Return the name of the switch."""
        return "JBL Smart Mode"

    @property
    def unique_id(self):
        """Return a unique ID for the switch."""
        return f"jbl_smart_mode_{self._entry.entry_id}"

    @property
    def is_on(self):
        """Return true if switch is on."""
        return self.coordinator.data.get("SmartMode") == "on"
    
    @property
    def icon(self):
        """Return the icon to use in the frontend."""
        return "mdi:surround-sound"
    
    @property
    def device_info(self):
        """Return device information about this entity."""
        return self.coordinator.device_info

    async def async_turn_on(self, **kwargs):
        """Turn the switch on."""
        await self.coordinator._send_command("surround")
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs):
        """Turn the switch off."""
        await self.coordinator._send_command("surround")
        await self.coordinator.async_request_refresh()

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


class PureVoiceModeSwitch(SwitchEntity):
    """Representation of a switch to control JBL PureVoice."""

    def __init__(self, entry: ConfigEntry, coordinator: Coordinator):
        """Initialize the switch."""
        self._entry = entry
        self._is_on = False
        self.coordinator = coordinator        
        self.entity_id = f"switch.{self.coordinator.device_info.get('name', 'jbl_integration').replace(' ', '_').lower()}_pure_voice"

    @property
    def name(self):
        """Return the name of the switch."""
        return "JBL Pure Voice"

    @property
    def unique_id(self):
        """Return a unique ID for the switch."""
        return f"jbl_pure_voice_{self._entry.entry_id}"

    @property
    def is_on(self):
        """Return true if switch is on."""
        return self.coordinator.data.get("PureVoice") == "on"
    
    @property
    def icon(self):
        """Return the icon to use in the frontend."""
        return "mdi:account-voice"
    
    @property
    def device_info(self):
        """Return device information about this entity."""
        return self.coordinator.device_info

    async def async_turn_on(self, **kwargs):
        """Turn the switch on."""
        await self.coordinator.setPureVoice(True)

    async def async_turn_off(self, **kwargs):
        """Turn the switch off."""
        await self.coordinator.setPureVoice(False)

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