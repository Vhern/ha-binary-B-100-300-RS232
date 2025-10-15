from __future__ import annotations
import glob, os
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from .const import (
    DOMAIN, CONF_PORT, CONF_BAUD, CONF_STATUS_CMD, CONF_POLL_SECONDS, CONF_SIZE,
    DEFAULT_BAUD, DEFAULT_POLL, DEFAULT_STATUS_CMD, DEFAULT_SIZE, SIZES,
)

def _serial_choices() -> list[str]:
    try:
        paths = (
            sorted(glob.glob("/dev/serial/by-id/*"))
            + sorted(glob.glob("/dev/ttyUSB*"))
            + sorted(glob.glob("/dev/ttyACM*"))
        )
        out, seen = [], set()
        for p in paths:
            if p not in seen and os.path.exists(p):
                seen.add(p); out.append(p)
        return out or ["/dev/ttyUSB0"]
    except Exception:
        return ["/dev/ttyUSB0"]

class BinaryMatrixConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="Binary HDMI Matrix", data=user_input)

        ports = _serial_choices()
        schema = vol.Schema({
            vol.Required(CONF_SIZE, default=DEFAULT_SIZE): vol.In(SIZES),
            vol.Required(CONF_PORT, default=ports[0]): vol.In(ports),
            vol.Required(CONF_BAUD, default=DEFAULT_BAUD): int,
            vol.Optional(CONF_STATUS_CMD, default=DEFAULT_STATUS_CMD): str,
            vol.Optional(CONF_POLL_SECONDS, default=DEFAULT_POLL): int,
        })
        return self.async_show_form(step_id="user", data_schema=schema)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return OptionsFlow(config_entry)

class OptionsFlow(config_entries.OptionsFlow):
    def __init__(self, entry):
        self.entry = entry

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        data = {**self.entry.data, **(self.entry.options or {})}
        ports = _serial_choices()
        current_port = data.get(CONF_PORT)
        if current_port and current_port not in ports:
            ports = [current_port] + ports
        default_port = current_port or ports[0]
        default_baud = int(data.get(CONF_BAUD, DEFAULT_BAUD))
        default_status = data.get(CONF_STATUS_CMD, DEFAULT_STATUS_CMD)
        default_poll = int(data.get(CONF_POLL_SECONDS, DEFAULT_POLL))
        default_size = data.get(CONF_SIZE, DEFAULT_SIZE if DEFAULT_SIZE in SIZES else SIZES[0])

        schema = vol.Schema({
            vol.Required(CONF_SIZE, default=default_size): vol.In(SIZES),
            vol.Required(CONF_PORT, default=default_port): vol.In(ports),
            vol.Required(CONF_BAUD, default=default_baud): int,
            vol.Optional(CONF_STATUS_CMD, default=default_status): str,
            vol.Optional(CONF_POLL_SECONDS, default=default_poll): int,
        })
        return self.async_show_form(step_id="init", data_schema=schema)
