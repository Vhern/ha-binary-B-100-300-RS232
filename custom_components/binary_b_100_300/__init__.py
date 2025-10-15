from __future__ import annotations
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.typing import ConfigType
from homeassistant.helpers import config_validation as cv
import voluptuous as vol
from .const import *

PLATFORMS = ["select", "switch"]  # sensors removed

async def async_setup(hass: HomeAssistant, config: ConfigType):
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    from .coordinator import MatrixCoordinator

    data = {**entry.data, **entry.options}
    size = data.get(CONF_SIZE, DEFAULT_SIZE)
    n = 8 if size == "8x8" else 4
    coord = MatrixCoordinator(
        hass,
        data[CONF_PORT],
        int(data.get(CONF_BAUD, DEFAULT_BAUD)),
        data.get(CONF_STATUS_CMD, DEFAULT_STATUS_CMD),
        int(data.get(CONF_POLL_SECONDS, DEFAULT_POLL)),
        n,
    )
    await coord.async_config_entry_first_refresh()
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {"coordinator": coord, "n": n}
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    schema_oi = vol.Schema({"output": vol.All(int, vol.Range(min=1, max=n)), "input": vol.All(int, vol.Range(min=1, max=n))})
    schema_o = vol.Schema({"output": vol.All(int, vol.Range(min=1, max=n))})

    async def handle_set_route(call):
        await coord.async_set_route(int(call.data["output"]), int(call.data["input"]))

    async def handle_output_on(call):
        await coord.async_output_on(int(call.data["output"]))

    async def handle_output_off(call):
        await coord.async_output_off(int(call.data["output"]))

    async def handle_next(call):
        await coord.async_next_input(int(call.data["output"]))

    async def handle_prev(call):
        await coord.async_prev_input(int(call.data["output"]))

    async def handle_power(call):
        val = str(call.data.get("state", "")).lower() in ("on", "1", "true")
        await coord.async_system_power(val)

    async def handle_send_raw(call):
        payload = call.data["data"]
        await coord.ser.write(hass, f"{payload}".encode("latin1"))

    async def handle_factory_reset(call):
        await coord.async_factory_reset()

    async def handle_refresh(call):
        await coord.force_refresh()

    async def handle_query_info(call):
        await coord.query_info()

    hass.services.async_register(DOMAIN, "set_route", handle_set_route, schema=schema_oi)
    hass.services.async_register(DOMAIN, "output_on", handle_output_on, schema=schema_o)
    hass.services.async_register(DOMAIN, "output_off", handle_output_off, schema=schema_o)
    hass.services.async_register(DOMAIN, "next_input", handle_next, schema=schema_o)
    hass.services.async_register(DOMAIN, "prev_input", handle_prev, schema=schema_o)
    hass.services.async_register(DOMAIN, "system_power", handle_power, schema=vol.Schema({"state": cv.boolean}))
    hass.services.async_register(DOMAIN, "send_raw", handle_send_raw, schema=vol.Schema({"data": str}))
    hass.services.async_register(DOMAIN, "factory_reset", handle_factory_reset)
    hass.services.async_register(DOMAIN, "refresh", handle_refresh)
    hass.services.async_register(DOMAIN, "query_info", handle_query_info)
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    data = hass.data[DOMAIN].pop(entry.entry_id, None)
    if data:
        await data["coordinator"].ser.async_close(hass)
    return True
