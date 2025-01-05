"""Sensor platform for JBL integration."""
import aiohttp
import async_timeout
import logging
from datetime import timedelta
from homeassistant.helpers.entity import Entity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.const import PERCENTAGE
from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)

from .const import DOMAIN
from .coordinator import Coordinator

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    """Set up the JBL sensor platform."""

    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    
    entityArray = []
    entityArray.append(JBLSensor(coordinator,entry,"play_medium","Play Medium","mdi:soundbar"))
    entityArray.append(JBLSensor(coordinator,entry,"volume_level","Volume","mdi:volume-high"))
    entityArray.append(JBLSensor(coordinator,entry,"transport_state","Transport State","mdi:state-machine"))
    entityArray.append(JBLSensor(coordinator,entry,"transport_status","Transport Status","mdi:information"))
    entityArray.append(JBLSensor(coordinator,entry,"mute","mute","mdi:volume-mute"))
    entityArray.append(JBLSensor(coordinator,entry,"track_duration","Track Duration","mdi:information"))
    entityArray.append(JBLSensor(coordinator,entry,"track","Track","mdi:information"))
    entityArray.append(JBLSensor(coordinator,entry,"channel","Channel","mdi:information"))
    
    if "Rears" in coordinator.data:
        entityArray.append(JBLRearSensor(coordinator,entry,0))
        entityArray.append(JBLRearSensor(coordinator,entry,1))
        
    async_add_entities(entityArray)

    
class JBLSensor(Entity):
    """Representation of a sensor to get JBL PlayMedium."""

    def __init__(self, coordinator, entry, infoString, name, icon):
        """Initialize the sensor."""
        self.coordinator = coordinator
        self._entry = entry
        self.entityName = name
        self.entityicon = icon
        self.entity_id = f"button.{self.coordinator.device_info.get("name", "jbl_integration").replace(' ', '_').lower()}_{self.entityName.replace(' ', '_').lower()}"
        self.infoString = infoString

    @property
    def name(self):
        """Return the name of the sensor."""
        return self.entityName

    @property
    def entity_registry_enabled_default(self) -> bool:
        """Return whether the entity should be enabled when first added to the entity registry."""
        return False  # Disable the sensor by default

    @property
    def state(self):
        """Return the state of the sensor."""
        return self.coordinator.data.get(self.infoString)

    @property
    def icon(self):
        """Return the icon to use in the frontend."""
        return self.entityicon

    @property
    def enabled(self):
        return false

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
        return self.coordinator.device_info


    async def async_added_to_hass(self):
        """When entity is added to hass."""
        self.async_on_remove(self.coordinator.async_add_listener(self.async_write_ha_state))

    async def async_update(self):
        """Update the sensor."""
        await self.coordinator.async_request_refresh()

class JBLRearSensor(Entity):
    """Representation of a battery for the rear speakers of the  JBL."""

    def __init__(self, coordinator, entry, arrayNumber: int):
        """Initialize the sensor."""
        self.coordinator = coordinator
        self.number = arrayNumber
        self._entry = entry
        self.entityName = "Battery"
        self.entity_id = f"sensor.{self.coordinator.device_info.get("name", "jbl_integration").replace(' ', '_').lower()}_{self.entityName.replace(' ', '_').lower()}"

    @property
    def name(self):
        """Return the name of the sensor."""
        return self.entityName
    
    @property
    def device_class(self):
        return SensorDeviceClass.BATTERY

    @property
    def unit_of_measurement(self):
        return PERCENTAGE

    @property
    def entity_registry_enabled_default(self) -> bool:
        """Return whether the entity should be enabled when first added to the entity registry."""
        return True  # Disable the sensor by default

    @property
    def state(self):
        """Return the state of the sensor."""
        return self.coordinator.data["Rears"][self.number]["capicity"]

    @property
    def enabled(self):
        return True

    @property
    def unique_id(self):
        """Return a unique ID for the sensor."""
        return f"jbl_{self._entry.entry_id}_{self.coordinator.data["Rears"][self.number]["channel"].lower()}_{self.entityName.replace(' ', '_').lower()}"

    @property
    def should_poll(self):
        """No polling needed."""
        return False

    @property
    def device_info(self):
        """Return device information about this entity."""
        BaseDevice = self.coordinator.device_info.copy()
        BaseDevice["name"] = BaseDevice["name"] + " Rear Speaker " + self.coordinator.data["Rears"][self.number]["channel"].title()
        BaseDevice["identifiers"] = {(DOMAIN,f"{self.coordinator.device_info.get("name", "jbl_integration").replace(' ', '_').lower()}_{self.coordinator.data["Rears"][self.number]["channel"]}")}
        return BaseDevice

    async def async_added_to_hass(self):
        """When entity is added to hass."""
        self.async_on_remove(self.coordinator.async_add_listener(self.async_write_ha_state))

    async def async_update(self):
        """Update the sensor."""
        await self.coordinator.async_request_refresh()
