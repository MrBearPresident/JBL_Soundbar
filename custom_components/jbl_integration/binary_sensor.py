"""Binary Sensor platform for JBL integration."""
import logging
from homeassistant.components.binary_sensor import BinarySensorEntity, BinarySensorDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    """Set up the JBL binary sensor platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]

    if "Rears" in coordinator.data:
        async_add_entities([
            JBLChargingSensor(coordinator, entry, 0),
            JBLDockedSensor(coordinator, entry, 0),
            JBLOnlineSensor(coordinator, entry, 0),
            JBLChargingSensor(coordinator, entry, 1),
            JBLDockedSensor(coordinator, entry, 1),
            JBLOnlineSensor(coordinator, entry, 1),
        ])

class JBLChargingSensor(BinarySensorEntity):
    """Representation of a charging sensor for the JBL rear speakers."""

    def __init__(self, coordinator, entry, arrayNumber: int):
        """Initialize the sensor."""
        self.coordinator = coordinator
        self.number = arrayNumber
        self._entry = entry
        self.entityName = "Charging"
        self.entity_id = f"binary_sensor.{self.coordinator.device_info.get('name', 'jbl_integration').replace(' ', '_').lower()}_{self.entityName.replace(' ', '_').lower()}"

    @property
    def name(self):
        """Return the name of the sensor."""
        return self.entityName

    @property
    def is_on(self):
        """Return true if the sensor is on."""
        return self.coordinator.data["Rears"][self.number]["charging"]

    @property
    def device_class(self):
        return BinarySensorDeviceClass.BATTERY_CHARGING

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
        BaseDevice["name"] = f"{BaseDevice['name']} Rear Speaker {self.coordinator.data['Rears'][self.number]['channel'].title()}"
        BaseDevice["identifiers"] = {(DOMAIN, f"{self.coordinator.device_info.get('name', 'jbl_integration').replace(' ', '_').lower()}_{self.coordinator.data['Rears'][self.number]['channel']}")}
        return BaseDevice

    async def async_added_to_hass(self):
        """When entity is added to hass."""
        self.async_on_remove(self.coordinator.async_add_listener(self.async_write_ha_state))

    async def async_update(self):
        """Update the sensor."""
        await self.coordinator.async_request_refresh()

class JBLDockedSensor(BinarySensorEntity):
    """Representation of a docked sensor for the JBL rear speakers."""

    def __init__(self, coordinator, entry, arrayNumber: int):
        """Initialize the sensor."""
        self.coordinator = coordinator
        self.number = arrayNumber
        self._entry = entry
        self.entityName = "Docked"
        self.entity_id = f"binary_sensor.{self.coordinator.device_info.get('name', 'jbl_integration').replace(' ', '_').lower()}_{self.entityName.replace(' ', '_').lower()}"

    @property
    def name(self):
        """Return the name of the sensor."""
        return self.entityName

    @property
    def is_on(self):
        """Return true if the sensor is on."""
        return self.coordinator.data["Rears"][self.number]["docked"]

    @property
    def device_class(self):
        return BinarySensorDeviceClass.PLUG

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
        BaseDevice["name"] = f"{BaseDevice['name']} Rear Speaker {self.coordinator.data['Rears'][self.number]['channel'].title()}"
        BaseDevice["identifiers"] = {(DOMAIN, f"{self.coordinator.device_info.get('name', 'jbl_integration').replace(' ', '_').lower()}_{self.coordinator.data['Rears'][self.number]['channel']}")}
        return BaseDevice

    async def async_added_to_hass(self):
        """When entity is added to hass."""
        self.async_on_remove(self.coordinator.async_add_listener(self.async_write_ha_state))

    async def async_update(self):
        """Update the sensor."""
        await self.coordinator.async_request_refresh()

class JBLOnlineSensor(BinarySensorEntity):
    """Representation of an online sensor for the JBL rear speakers."""

    def __init__(self, coordinator, entry, arrayNumber: int):
        """Initialize the sensor."""
        self.coordinator = coordinator
        self.number = arrayNumber
        self._entry = entry
        self.entityName = "Online"
        self.entity_id = f"binary_sensor.{self.coordinator.device_info.get('name', 'jbl_integration').replace(' ', '_').lower()}_{self.entityName.replace(' ', '_').lower()}"

    @property
    def name(self):
        """Return the name of the sensor."""
        return self.entityName

    @property
    def is_on(self):
        """Return true if the sensor is on."""
        return self.coordinator.data["Rears"][self.number]["status"] == "online"

    @property
    def device_class(self):
        return BinarySensorDeviceClass.CONNECTIVITY

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
        BaseDevice["name"] = f"{BaseDevice['name']} Rear Speaker {self.coordinator.data['Rears'][self.number]['channel'].title()}"
        BaseDevice["identifiers"] = {(DOMAIN, f"{self.coordinator.device_info.get('name', 'jbl_integration').replace(' ', '_').lower()}_{self.coordinator.data['Rears'][self.number]['channel']}")}
        return BaseDevice

    async def async_added_to_hass(self):
        """When entity is added to hass."""
        self.async_on_remove(self.coordinator.async_add_listener(self.async_write_ha_state))

    async def async_update(self):
        """Update the sensor."""
        await self.coordinator.async_request_refresh()  