from bleak.backends.device import BLEDevice
from bleak.backends.scanner import AdvertisementData

from ..devicebase import DeviceBase
from ..packet import Packet
from ..pb import dev_apl_comm_pb2
from ..props import ProtobufProps, computed_field, pb_field, proto_attr_mapper
from ..props.transforms import pround

pb = proto_attr_mapper(dev_apl_comm_pb2.DisplayPropertyUpload)


def _port_enabled(value: int) -> bool:
    """EcoFlow uses 1 for enabled and 2 for disabled in port state fields."""
    return value == 1


class Device(DeviceBase, ProtobufProps):
    """Rapid Pro 320W GaN charger"""

    SN_PREFIX = (b"P521",)
    NAME_PREFIX = "EF-DC-320-"
    AUTH_USER_ID = "homeassistant"
    AUTH_TOKEN_LOWERCASE = True

    battery_level = pb_field(pb.cms_batt_soc)
    state_of_health = pb_field(pb.cms_batt_soh)
    cell_temperature = pb_field(pb.cms_batt_temp)
    input_power = pb_field(pb.pow_in_sum_w, pround(2))
    output_power = pb_field(pb.pow_out_sum_w, pround(2))
    remaining_time_charging = pb_field(pb.cms_chg_rem_time)
    remaining_time_discharging = pb_field(pb.cms_dsg_rem_time)
    battery_charge_limit_min = pb_field(pb.cms_min_dsg_soc)
    battery_charge_limit_max = pb_field(pb.cms_max_chg_soc)

    error_code = pb_field(pb.errcode)
    _device_error_info = pb_field(pb.dev_errcode_list)

    usb_c1_port_enabled = pb_field(pb.typec1_port_enable, _port_enabled)
    usb_c2_port_enabled = pb_field(pb.typec2_port_enable, _port_enabled)
    usb_c3_port_enabled = pb_field(pb.typec3_port_enable, _port_enabled)
    usb_c4_port_enabled = pb_field(pb.typec4_port_enable, _port_enabled)
    usb_a1_port_enabled = pb_field(pb.usb1_port_enable, _port_enabled)
    pogo_port_enabled = pb_field(pb.pogopin_port_enable, _port_enabled)

    usb_c1_power = pb_field(pb.usb_typec1_display_info.usb_pow, pround(2))
    usb_c1_voltage = pb_field(pb.usb_typec1_display_info.usb_vol, pround(2))
    usb_c1_current = pb_field(pb.usb_typec1_display_info.usb_amp, pround(2))

    usb_c2_power = pb_field(pb.usb_typec2_display_info.usb_pow, pround(2))
    usb_c2_voltage = pb_field(pb.usb_typec2_display_info.usb_vol, pround(2))
    usb_c2_current = pb_field(pb.usb_typec2_display_info.usb_amp, pround(2))

    usb_c3_power = pb_field(pb.usb_typec3_display_info.usb_pow, pround(2))
    usb_c3_voltage = pb_field(pb.usb_typec3_display_info.usb_vol, pround(2))
    usb_c3_current = pb_field(pb.usb_typec3_display_info.usb_amp, pround(2))

    usb_c4_power = pb_field(pb.usb_typec4_display_info.usb_pow, pround(2))
    usb_c4_voltage = pb_field(pb.usb_typec4_display_info.usb_vol, pround(2))
    usb_c4_current = pb_field(pb.usb_typec4_display_info.usb_amp, pround(2))

    usb_a1_power = pb_field(pb.usb_typeA1_display_info.usb_pow, pround(2))
    usb_a1_voltage = pb_field(pb.usb_typeA1_display_info.usb_vol, pround(2))
    usb_a1_current = pb_field(pb.usb_typeA1_display_info.usb_amp, pround(2))

    pogo_power = pb_field(pb.pogopin_1_display_info.usb_pow, pround(2))
    pogo_voltage = pb_field(pb.pogopin_1_display_info.usb_vol, pround(2))
    pogo_current = pb_field(pb.pogopin_1_display_info.usb_amp, pround(2))

    def __init__(
        self, ble_dev: BLEDevice, adv_data: AdvertisementData, sn: str
    ) -> None:
        super().__init__(ble_dev, adv_data, sn)

    @classmethod
    def check(cls, sn: bytes) -> bool:
        return sn[:4] in cls.SN_PREFIX

    @computed_field
    def device_error_codes(self) -> list[int]:
        if self._device_error_info is None:
            return []
        return list(self._device_error_info.dev_errcode)

    @computed_field
    def error_occurred(self) -> bool:
        return bool(self.error_code) or any(self.device_error_codes)

    async def packet_parse(self, data: bytes):
        return Packet.from_bytes(data, xor_payload=True)

    async def data_parse(self, packet: Packet):
        self.reset_updated()
        processed = False

        if packet.src == 0x02 and packet.cmd_set == 0xFE and packet.cmd_id == 0x15:
            processed = (
                self.update_from_bytes(
                    dev_apl_comm_pb2.DisplayPropertyUpload, packet.payload
                )
                is not None
            )

        self._notify_updated()
        return processed
