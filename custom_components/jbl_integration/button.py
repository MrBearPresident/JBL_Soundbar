"""Button platform for JBL integration."""
import async_timeout
import logging
from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .coordinator import Coordinator

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    """Set up the JBL button platform."""

    
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]

    async_add_entities([
        JBLButton(coordinator,entry,"power","Power","mdi:power"),
        JBLButton(coordinator,entry,"mute","Mute","mdi:volume-off"),
        JBLButton(coordinator,entry,"volumeUp","Increase Volume","mdi:volume-plus"),
        JBLButton(coordinator,entry,"volumeDown","Lower Volume","mdi:volume-minus"),
        JBLButton(coordinator,entry,"musicPlayPause","Play/Pause","mdi:play-pause"),
        JBLButton(coordinator,entry,"smart_triger","Smart","mdi:heart-box"),
        JBLButton(coordinator,entry,"calibration","Calibration","mdi:calculator-variant"),
        JBLButton(coordinator,entry,"keyRear","Rear","mdi:numeric-2-box-multiple"),
        JBLButton(coordinator,entry,"bassboost","Bass","mdi:equalizer"),
        JBLButton(coordinator,entry,"keyAtmosLevel","Atmos","mdi:equalizer"),
        JBLButton(coordinator,entry,"source-hdmi-switch","HDMI","mdi:video-input-hdmi"),
        JBLButton(coordinator,entry,"bluetooth","Bluetooth","mdi:bluetooth"),
        JBLButton(coordinator,entry,"source-tv","TV","mdi:television-box"),
    ])

class JBLButton(ButtonEntity):
    """Base class for a JBL button."""

    def __init__(self, coordinator, entry, actionstring, name, icon):
        """Initialize the sensor."""
        self.coordinator:Coordinator = coordinator
        self._entry = entry
        self.entityName = name
        self.entityicon = icon
        self.actionstring = actionstring

    @property
    def name(self):
        """Return the name of the sensor."""
        return self.entityName

    @property
    def entity_registry_enabled_default(self) -> bool:
        """Return whether the entity should be enabled when first added to the entity registry."""
        return False  # Disable the sensor by default

    @property
    def icon(self):
        """Return the icon to use in the frontend."""
        return self.entityicon

    @property
    def unique_id(self):
        """Return a unique ID for the sensor."""
        return f"jbl_800_Button{self.entityName.replace(' ', '')}_{self._entry.entry_id}"

    @property
    def device_info(self):
        """Return device information about this entity."""
        return self.coordinator.device_info

    async def async_press(self) -> None:
        """Handle the button press."""
        await self.coordinator._send_command(self.actionstring)
