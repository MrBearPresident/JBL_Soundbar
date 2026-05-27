"""Select platform for JBL integration."""
import asyncio
import logging
from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .coordinator import Coordinator
from .entity import build_entity_id

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    """Set up the JBL select platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]

    entities = []
    if coordinator.data.get("eq_preset_map"):
        entities.append(JBLEQPresetSelect(entry, coordinator))

    async_add_entities(entities)


class JBLEQPresetSelect(SelectEntity):
    """Select entity for JBL EQ presets."""

    def __init__(self, entry: ConfigEntry, coordinator: Coordinator):
        """Initialize the select."""
        self._entry = entry
        self.coordinator = coordinator
        self.entity_id = build_entity_id(
            "select",
            self.coordinator.device_info.get("name", "jbl_integration"),
            "eq_preset",
        )

    @property
    def name(self):
        """Return the name of the select."""
        return "JBL EQ Preset"

    @property
    def unique_id(self):
        """Return a unique ID for the select."""
        return f"jbl_eq_preset_{self._entry.entry_id}"

    @property
    def icon(self):
        """Return the icon."""
        return "mdi:tune-variant"

    @property
    def device_info(self):
        """Return device information about this entity."""
        return self.coordinator.device_info

    @property
    def options(self):
        """Return the list of available EQ preset names."""
        preset_map = self.coordinator.data.get("eq_preset_map", {})
        return list(preset_map.values()) if preset_map else []

    @property
    def current_option(self):
        """Return the currently active EQ preset name."""
        return self.coordinator.data.get("eq_active_preset")

    async def async_select_option(self, option: str):
        """Set the EQ preset."""
        preset_map = self.coordinator.data.get("eq_preset_map", {})
        for eq_id, eq_name in preset_map.items():
            if eq_name == option:
                await self.coordinator.setActiveEQPreset(eq_id)
                # Optimistic update
                self.coordinator.data["eq_active_preset"] = eq_name
                self.coordinator.data["eq_active_id"] = eq_id
                self.async_write_ha_state()
                # Delay then refresh to confirm
                await asyncio.sleep(1)
                await self.coordinator.async_request_refresh()
                return
        _LOGGER.error("EQ preset not found: %s", option)

    @property
    def should_poll(self):
        """No polling needed."""
        return False

    async def async_added_to_hass(self):
        """When entity is added to hass."""
        self.async_on_remove(self.coordinator.async_add_listener(self.async_write_ha_state))

    async def async_update(self):
        """Update the entity."""
        await self.coordinator.async_request_refresh()
