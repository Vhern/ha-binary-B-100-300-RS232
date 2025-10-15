from __future__ import annotations
from homeassistant.components.switch import SwitchEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.config_entries import ConfigEntry
from .const import DOMAIN
from .coordinator import MatrixCoordinator
from .entity import MatrixEntity

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, add_entities: AddEntitiesCallback):
    coord: MatrixCoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    add_entities([OutputPowerSwitch(coord, i+1) for i in range(coord.n)])

class OutputPowerSwitch(MatrixEntity, SwitchEntity):
    def __init__(self, coord: MatrixCoordinator, out_idx: int):
        MatrixEntity.__init__(self, coord)
        self._out = out_idx
        self._attr_name = f"Output {out_idx} Power"
        self._attr_unique_id = f"{coord.uid}_output_{out_idx}_power"

    @property
    def is_on(self) -> bool:
        return self._coord.power[self._out - 1]

    async def async_turn_on(self, **kwargs):
        await self._coord.async_output_on(self._out)

    async def async_turn_off(self, **kwargs):
        await self._coord.async_output_off(self._out)

    @property
    def should_poll(self) -> bool:
        return False

    async def async_added_to_hass(self):
        self.async_on_remove(self._coord.async_add_listener(self.async_write_ha_state))
