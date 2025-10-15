from __future__ import annotations
import asyncio, logging, re
from typing import Optional
import serial
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

class MatrixSerial:
    def __init__(self, port: str, baud: int):
        self._port = port
        self._baud = baud
        self._ser: Optional[serial.Serial] = None
        self._lock = asyncio.Lock()

    async def async_open(self, hass: HomeAssistant):
        def _open():
            return serial.Serial(
                self._port, self._baud,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                xonxoff=False, rtscts=False,
                timeout=1, write_timeout=1,
            )
        self._ser = await hass.async_add_executor_job(_open)

    async def async_close(self, hass: HomeAssistant):
        if self._ser:
            await hass.async_add_executor_job(self._ser.close)
            self._ser = None

    async def write(self, hass: HomeAssistant, payload: bytes):
        async with self._lock:
            if not self._ser:
                await self.async_open(hass)
            def _w():
                self._ser.write(payload)
                self._ser.flush()
            await hass.async_add_executor_job(_w)
            await asyncio.sleep(1.5)  # device needs spacing


class MatrixCoordinator(DataUpdateCoordinator):
    def __init__(self, hass: HomeAssistant, port: str, baud: int, status_cmd: str, poll: int, size: int):
        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=None)
        self.ser = MatrixSerial(port, baud)
        self.status_cmd = (status_cmd or "").strip()  # STMAP
        self.poll_seconds = int(poll)
        self.n = int(size)  # 4 or 8
        self.routes = [1 for _ in range(self.n)]  # keep last input when off
        self.power = [True for _ in range(self.n)]
        self.fw: Optional[str] = None
        self.ip: Optional[str] = None
        self._poll_task: Optional[asyncio.Task] = None

        # device identity
        port_id = re.sub(r"[^A-Za-z0-9_.-]", "_", port)
        self.uid = f"{port_id}_{self.n}x{self.n}"
        self.mfr = "Binary"
        self.model = f"B-100/300 {self.n}x{self.n}"
        self.name = "Binary HDMI Matrix (RS232)"

        # poll coordination
        self._busy = 0

    async def async_config_entry_first_refresh(self):
        await self.ser.async_open(self.hass)
        if self.status_cmd:
            self._poll_task = asyncio.create_task(self._poll_loop())
        await self.query_info()
        await self._update_from_status()
        self.async_set_updated_data(self.routes.copy())

    async def _poll_loop(self):
        while True:
            try:
                if self._busy:
                    await asyncio.sleep(self.poll_seconds)
                    continue
                await self._update_from_status()
                self.async_set_updated_data(self.routes.copy())
            except Exception as e:
                _LOGGER.debug("Status poll failed: %s", e)
            await asyncio.sleep(max(1, self.poll_seconds))

    async def force_refresh(self):
        await self._update_from_status()
        self.async_set_updated_data(self.routes.copy())

    async def _update_from_status(self):
        if not self.status_cmd:
            return
        # send STMAP and read once
        async with self.ser._lock:
            if not self.ser._ser:
                await self.ser.async_open(self.hass)

            def _io():
                self.ser._ser.write(f"{self.status_cmd}\r".encode("ascii"))
                self.ser._ser.flush()
                data = self.ser._ser.read(4096)
                return data.decode(errors="ignore")

            resp = await self.hass.async_add_executor_job(_io)

        for line in (l.strip() for l in resp.splitlines() if l.strip()):
            if not (line.startswith("o") and "i" in line):
                continue
            try:
                o = int(line[1:3])
                i = int(line[line.index('i')+1:line.index('i')+3])
            except Exception:
                continue
            if 1 <= o <= self.n:
                if i == 0:
                    self.power[o-1] = False
                elif 1 <= i <= self.n:
                    self.routes[o-1] = i
                    self.power[o-1] = True

    async def _send(self, cmd: bytes):
        self._busy += 1
        try:
            await self.ser.write(self.hass, cmd)
        finally:
            self._busy -= 1

    # routing
    async def async_set_route(self, out_idx: int, in_num: int):
        if not (1 <= out_idx <= self.n and 1 <= in_num <= self.n):
            return
        await self._send(f"{out_idx:02d}{in_num:02d}\r".encode("ascii"))
        self.routes[out_idx - 1] = in_num
        self.power[out_idx - 1] = True
        self.async_set_updated_data(self.routes.copy())

    async def async_next_input(self, out_idx: int):
        if not (1 <= out_idx <= self.n):
            return
        await self._send(f"{out_idx:02d}+\r".encode("ascii"))
        await self._update_from_status()

    async def async_prev_input(self, out_idx: int):
        if not (1 <= out_idx <= self.n):
            return
        await self._send(f"{out_idx:02d}-\r".encode("ascii"))
        await self._update_from_status()

    # output power
    async def async_output_on(self, out_idx: int):
        if not (1 <= out_idx <= self.n):
            return
        await self._send(f"{out_idx:02d}L\r".encode("ascii"))
        self.power[out_idx - 1] = True
        if self.routes[out_idx - 1] < 1:
            self.routes[out_idx - 1] = 1
        self.async_set_updated_data(self.routes.copy())

    async def async_output_off(self, out_idx: int):
        if not (1 <= out_idx <= self.n):
            return
        await self._send(f"{out_idx:02d}00\r".encode("ascii"))
        self.power[out_idx - 1] = False
        self.async_set_updated_data(self.routes.copy())

    # system power
    async def async_system_power(self, on: bool):
        await self._send(("01\r" if on else "00\r").encode("ascii"))

    # info (firmware/IP; best-effort)
    async def query_info(self):
        try:
            async with self.ser._lock:
                if not self.ser._ser:
                    await self.ser.async_open(self.hass)

                def _fw():
                    self.ser._ser.write(b"VR\r")
                    self.ser._ser.flush()
                    data = self.ser._ser.read(256)
                    return data.decode(errors="ignore")

                fw = await self.hass.async_add_executor_job(_fw)
                if "FW:" in fw:
                    self.fw = fw.strip().splitlines()[0]
        except Exception:
            pass

        try:
            async with self.ser._lock:
                if not self.ser._ser:
                    await self.ser.async_open(self.hass)

                def _ip():
                    self.ser._ser.write(b"IP\r")
                    self.ser._ser.flush()
                    data = self.ser._ser.read(256)
                    return data.decode(errors="ignore")

                ip = await self.hass.async_add_executor_job(_ip)
                ip = ip.strip().splitlines()[0] if ip else ""
                self.ip = ip if ip and ip[0].isdigit() else None
        except Exception:
            pass

    async def async_factory_reset(self):
        await self._send(b"FASET\r")

    async def _async_update_data(self):
        return self.routes
