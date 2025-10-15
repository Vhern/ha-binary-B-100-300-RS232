from __future__ import annotations
from homeassistant.components.select import SelectEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.config_entries import ConfigEntry
from .const import DOMAIN
from .coordinator import MatrixCoordinator
from .entity import MatrixEntity

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, add_entities: AddEntitiesCallback):
    coord: MatrixCoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    n = coord.n
    options = [f"Input {i}" for i in range(1, n + 1)]  # no "Off"
    add_entities([OutputSelect(coord, i+1, options) for i in range(n)])

class OutputSelect(MatrixEntity, SelectEntity):
    def __init__(self, coord: MatrixCoordinator, out_idx: int, options: list[str]):
        MatrixEntity.__init__(self, coord)
        self._out = out_idx
        self._attr_name = f"Output {out_idx} Source"
        self._attr_unique_id = f"{coord.uid}_output_{out_idx}_source"
        self._attr_options = options

    @property
    def current_option(self):
        val = self._coord.routes[self._out - 1] or 1  # keep last input; default to 1 if unknown
        return self._attr_options[val - 1]

    async def async_select_option(self, option: str):
        idx = self._attr_options.index(option) + 1
        await self._coord.async_set_route(self._out, idx)

    @property
    def should_poll(self) -> bool:
        return False

    async def async_added_to_hass(self):
        self.async_on_remove(self._coord.async_add_listener(self.async_write_ha_state))