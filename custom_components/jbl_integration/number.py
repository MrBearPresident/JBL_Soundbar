"""Number platform for JBL integration."""
import async_timeout
import logging
from homeassistant.components.number import NumberEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.event import async_track_state_change

from .const import DOMAIN
from .coordinator import Coordinator

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    """Set up the JBL switch platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]

    entityArray = []
    entityArray.append(JBLVolumeNumber(entry, coordinator))
    if coordinator.newFirmware:
        entityArray.append(JBLEqNumber(entry, coordinator," 125Hz"))
        entityArray.append(JBLEqNumber(entry, coordinator," 250Hz"))
        entityArray.append(JBLEqNumber(entry, coordinator," 500Hz"))
        entityArray.append(JBLEqNumber(entry, coordinator,"1000Hz"))
        entityArray.append(JBLEqNumber(entry, coordinator,"2000Hz"))
        entityArray.append(JBLEqNumber(entry, coordinator,"4000Hz"))
        entityArray.append(JBLEqNumber(entry, coordinator,"8000Hz"))
    else:
        entityArray.append(JBLEqNumber(entry, coordinator,"EQ_1_Low"))
        entityArray.append(JBLEqNumber(entry, coordinator,"EQ_2_Mid"))
        entityArray.append(JBLEqNumber(entry, coordinator,"EQ_3_High"))
    
    async_add_entities(entityArray)


class JBLVolumeNumber(NumberEntity):
    """Representation of a switch to control JBL power."""

    def __init__(self, entry: ConfigEntry, coordinator: Coordinator):
        """Initialize the switch."""
        self._entry = entry
        self._value  = 0
        self.coordinator = coordinator
        self.entity_id = f"number.{self.coordinator.device_info.get("name", "jbl_integration").replace(' ', '_').lower()}_{self.name.lower()}"
        

    @property
    def name(self):
        """Return the name of the Slider."""
        return "Volume"

    @property
    def unique_id(self):
        """Return a unique ID for the Slider."""
        return f"jbl_VolumeSlider_{self._entry.entry_id}"
        
    @property
    def device_info(self):
        """Return device information about this entity."""
        return self.coordinator.device_info

    @property
    def native_min_value(self):
        """Return the minimum value."""
        return 0

    @property
    def native_max_value(self):
        """Return the maximum value."""
        return 100

    @property
    def native_step(self):
        """Return the step size."""
        return 3

    @property
    def native_value(self):
        """Return the current value."""
        return self.coordinator.data.get("volume_level")

    @property
    def native_unit_of_measurement(self):
        """Return the unit of measurement."""
        return "%"

    @property
    def should_poll(self):
        """No polling needed."""
        return False



    async def async_set_native_value(self, value: float):
        await self.coordinator.setVolume(value)
        await self.coordinator.async_request_refresh()

    async def async_added_to_hass(self):
        """When entity is added to hass."""
        self.async_on_remove(self.coordinator.async_add_listener(self.async_write_ha_state))

    async def async_update(self):
        """Update the sensor."""
        await self.coordinator.async_request_refresh()

class JBLEqNumber(NumberEntity):
    """Representation of a number to control the EQ."""

    def __init__(self, entry: ConfigEntry, coordinator: Coordinator, eqLevel ):
        """Initialize the number."""
        self._entry = entry
        self._value  = 0        
        self.entityName = eqLevel
        self.coordinator = coordinator
        self.entity_id = f"number.{self.coordinator.device_info.get("name", "jbl_integration").replace(' ', '_').lower()}_{self.entityName.lower()}"

    @property
    def name(self):
        """Return the name of the Slider."""
        return self.entityName.replace('_',' ')

    @property
    def icon(self):
        return "mdi:equalizer"

    @property
    def unique_id(self):
        """Return a unique ID for the Slider."""
        return f"jbl_{self.entityName.replace('_','')}_{self._entry.entry_id}"
        
    @property
    def device_info(self):
        """Return device information about this entity."""
        
        return self.coordinator.device_info


    @property
    def native_min_value(self):
        """Return the minimum value."""
        minValue = -6 if ("EQ_1_Low" != self.entityName and " 125Hz" != self.entityName) else -9
        return minValue

    @property
    def native_max_value(self):
        """Return the maximum value."""
        return 6

    @property
    def native_step(self):
        """Return the step size."""
        return 0.5 if self.coordinator.newFirmware else 1

    @property
    def native_value(self):
        """Return the current value."""
        return self.coordinator.data.get(self.entityName.strip())

    @property
    def native_unit_of_measurement(self):
        """Return the unit of measurement."""
        return "db"

    @property
    def should_poll(self):
        """No polling needed."""
        return False

    async def async_set_native_value(self, value: float):
        await self.coordinator.setEQ(value,self.entityName.strip())
        await self.coordinator.async_request_refresh()

    async def async_added_to_hass(self):
        """When entity is added to hass."""
        self.async_on_remove(self.coordinator.async_add_listener(self.async_write_ha_state))

    async def async_update(self):
        """Update the sensor."""
        await self.coordinator.async_request_refresh()