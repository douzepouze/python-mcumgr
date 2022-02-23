import asyncio
import logging
from bleak import BleakClient

from mcumgr.smp import MgmtMsg, MgmtHdr

UUID_SERVICE = "8D53DC1D-1DB7-4CD3-868B-8A527460AA84"
UUID_CHARACT = "DA2E7828-FBCE-4E01-AE9E-261174997C48"

logger = logging.getLogger(__name__)


class SMPBLEClient:
    def __init__(self, address: str):
        self._client = BleakClient(address_or_ble_device=address)
        self._rx_queue = asyncio.Queue()

    @property
    def mtu_size(self):
        return self._client.mtu_size

    async def _rx_handler(self, sender, data):
        size = len(data)
        logger.debug(f"RX ({size}): {data}")
        await self._rx_queue.put(data)

    def _clear_rx_queue(self):
        for _ in range(self._rx_queue.qsize()):
            self._rx_queue.get_nowait()
            self._rx_queue.task_done()

    async def connect(self, timeout: int = 10):
        await self._client.connect(timeout=timeout)

        # BlueZ quirks to report correct MTU
        if self._client.__class__.__name__ == "BleakClientBlueZDBus":
            await self._client._acquire_mtu()

        logger.debug("BLE MTU on {} is {} bytes".format(self._client.address, self._client.mtu_size))

        await self._client.start_notify(UUID_CHARACT, self._rx_handler)

    async def disconnect(self):
        await self._client.stop_notify(UUID_CHARACT)
        await self._client.disconnect()

    async def send_request(self, request: MgmtMsg) -> MgmtMsg:
        self._clear_rx_queue()
        await self._client.write_gatt_char(UUID_CHARACT, request.to_bytes(), response=True)

        data = await self._rx_queue.get()
        hdr = MgmtHdr.from_bytes(data[:MgmtHdr.BYTE_SIZE])

        while len(data) < (hdr.nh_len + 8):
            data.extend(await self._rx_queue.get())

        return MgmtMsg.from_bytes(data)
