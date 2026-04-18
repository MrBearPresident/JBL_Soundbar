"""Initialize the JBL integration."""
import asyncio
import logging

from aiohttp import web
from homeassistant.components.http import KEY_HASS
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .coordinator import Coordinator
from homeassistant.helpers import config_validation as cv
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_PORT, CONF_UUID, CONF_ADDRESS, CONF_SCAN_INTERVAL

# Define the configuration schema for your integration
CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)
_LOGGER = logging.getLogger(__name__)

async def _handle_rendering_control_notify(request):
    """Handle RenderingControl GENA NOTIFY callbacks from JBL devices."""
    hass = request.app[KEY_HASS]
    entry_id = request.match_info["entry_id"]
    coordinator = hass.data.get(DOMAIN, {}).get(entry_id, {}).get("coordinator")
    if coordinator is None:
        return web.Response(status=404)

    body = await request.text()
    await coordinator.async_handle_rendering_control_notify(body)
    return web.Response(status=200)

def _register_rendering_control_event_route(hass):
    """Register unauthenticated NOTIFY callback route for GENA events."""
    hass.data.setdefault(DOMAIN, {})
    if hass.data[DOMAIN].get("rendering_control_event_route_registered"):
        return

    hass.http.app.router.add_route(
        "NOTIFY",
        f"/api/{DOMAIN}/{{entry_id}}/rendering_control",
        _handle_rendering_control_notify,
    )
    hass.data[DOMAIN]["rendering_control_event_route_registered"] = True

async def async_setup(hass: HomeAssistant, config: dict):
    """Set up the JBL integration."""
    _register_rendering_control_event_route(hass)
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up JBL integration from a config entry."""

    _LOGGER.debug("Setting up JBL Integration. Entry data: %s", str(entry.data))
    # Pass the IP address and polling rate to the Coordinator
    coordinator = Coordinator(entry.data.get(CONF_ADDRESS), entry.data.get(CONF_SCAN_INTERVAL),hass, entry)
    await coordinator._SetupDeviceInfo()
    await coordinator.async_config_entry_first_refresh()

    _register_rendering_control_event_route(hass)
    hass.data[DOMAIN][entry.entry_id] = {"coordinator": coordinator}
    await coordinator.async_start_rendering_control_events()

    await hass.config_entries.async_forward_entry_setups(entry, ["sensor", "switch","number","button","binary_sensor"])


    return True

async def async_migrate_entry(hass: HomeAssistant, entry: dict):
    """Migrate old entry."""

    if entry.version < 2:
        _LOGGER.error("Migrating JBL Integration entry to version 2. Current data: %s", entry.data)
        data = dict(entry.data) 
        if CONF_ADDRESS in data:
            _LOGGER.error("Migration to version 2: Migration 'address' not needed, key already present. Data: %s", entry.data)
            data.pop("ip_address", "192.168.1.1")
        else:
            data[CONF_ADDRESS] = data.pop("ip_address", "192.168.1.1")
            
         
        if CONF_SCAN_INTERVAL in data:
            _LOGGER.error("Migration to version 2: Migration 'scan_interval' not needed, key already present. Data: %s", entry.data)
            data.pop("ip_address", "192.168.1.1")
        else:
            data[CONF_SCAN_INTERVAL] =  data.pop("polling_rate", 5)
        
        hass.config_entries.async_update_entry(entry=entry, data=data, version=2)
        _LOGGER.error("Migration to version 2 successful . New data: %s", entry.data)
    return True


async def async_reload_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> None:
    """Reload the config entry."""
    _LOGGER.debug("Reloading JBL Integration. Entry data: %s", str(config_entry.data))
    
    if not await async_unload_entry(hass, config_entry):
        return
    await async_setup_entry(hass, config_entry)

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    await coordinator.async_stop_rendering_control_events()

    await hass.config_entries.async_forward_entry_unload(entry, "switch")
    await hass.config_entries.async_forward_entry_unload(entry, "sensor")
    await hass.config_entries.async_forward_entry_unload(entry, "number")
    await hass.config_entries.async_forward_entry_unload(entry, "button")
    await hass.config_entries.async_forward_entry_unload(entry, "binary_sensor")

    hass.data[DOMAIN].pop(entry.entry_id)
    return True
