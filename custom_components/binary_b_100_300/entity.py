from __future__ import annotations
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN
from .coordinator import MatrixCoordinator

class MatrixEntity(CoordinatorEntity[MatrixCoordinator]):
    _attr_has_entity_name = True

    def __init__(self, coord: MatrixCoordinator):
        super().__init__(coord)
        self._coord = coord

    @property
    def device_info(self):
        info = {
            "identifiers": {(DOMAIN, self._coord.uid)},
            "manufacturer": self._coord.mfr,
            "model": self._coord.model,
            "name": self._coord.name,
            "sw_version": self._coord.fw,
        }
        if self._coord.ip:
            info["configuration_url"] = f"http://{self._coord.ip}"
        return info