"""Initialize the JBL integration."""
import asyncio
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .coordinator import Coordinator

async def async_setup(hass: HomeAssistant, config: dict):
    """Set up the JBL integration."""
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up JBL integration from a config entry."""

    # Retrieve the IP address and polling rate from the config entry
    ip_address = entry.data.get("ip_address")
    polling_rate = entry.data.get("polling_rate", 5)

    # Pass the IP address and polling rate to the Coordinator
    coordinator = Coordinator(hass, entry, ip_address, polling_rate)
    await coordinator._SetupDeviceInfo()
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {"coordinator": coordinator}

    await hass.config_entries.async_forward_entry_setups(entry, ["sensor", "switch","number","button"])


    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    await hass.config_entries.async_forward_entry_unload(entry, "switch")
    await hass.config_entries.async_forward_entry_unload(entry, "sensor")
    await hass.config_entries.async_forward_entry_unload(entry, "number")
    await hass.config_entries.async_forward_entry_unload(entry, "button")

    hass.data[DOMAIN].pop(entry.entry_id)
    return True
