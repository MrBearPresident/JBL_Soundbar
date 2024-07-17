"""Sensor platform for JBL integration."""
import aiohttp
import async_timeout
import logging
from datetime import timedelta
from homeassistant.helpers.entity import Entity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import DOMAIN
from .coordinator import Coordinator

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    """Set up the JBL sensor platform."""

    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]

    instanceArray = []
    instanceArray.append(["play_medium","Play Medium","mdi:soundbar"])
    instanceArray.append(["volume_level","Volume","mdi:volume-high"])

    async_add_entities([
        JBLSensor(coordinator,entry,"play_medium","Play Medium","mdi:soundbar"),
        JBLSensor(coordinator,entry,"volume_level","Volume","mdi:volume-high"),
        #JBLPlayMediumSensor(coordinator, entry),
        #JBLVolumeLevelSensor(coordinator, entry),
        # Add other sensors here
    ])


    
class JBLSensor(Entity):
    """Representation of a sensor to get JBL PlayMedium."""

    def __init__(self, coordinator, entry, infoString, name, icon):
        """Initialize the sensor."""
        self.coordinator = coordinator
        self._entry = entry
        self.entityName = name
        self.entityicon = icon
        self.infoString = infoString

    @property
    def name(self):
        """Return the name of the sensor."""
        return self.entityName

    @property
    def state(self):
        """Return the state of the sensor."""
        return self.coordinator.data.get(self.infoString)

    @property
    def icon(self):
        """Return the icon to use in the frontend."""
        return self.entityicon

    @property
    def unique_id(self):
        """Return a unique ID for the sensor."""
        return f"jbl_800_{self.infoString.replace('_', '')}_{self._entry.entry_id}"

    @property
    def should_poll(self):
        """No polling needed."""
        return False

    @property
    def device_info(self):
        """Return device information about this entity."""
        return {
            "identifiers": {(DOMAIN, self._entry.entry_id)},
            "name": "JBL Bar 800",
            "manufacturer": "HARMAN International Industries",
            "model": "JBL Bar 800",
        }

    async def async_added_to_hass(self):
        """When entity is added to hass."""
        self.async_on_remove(self.coordinator.async_add_listener(self.async_write_ha_state))

    async def async_update(self):
        """Update the sensor."""
        await self.coordinator.async_request_refresh()

