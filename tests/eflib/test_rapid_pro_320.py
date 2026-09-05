import pytest
from pytest_mock import MockerFixture

from custom_components.ef_ble.eflib.devices.rapid_pro_320 import Device
from custom_components.ef_ble.eflib.packet import Packet


@pytest.fixture
def display_packet():
    """Captured authenticated Rapid Pro 320W DisplayPropertyUpload packet."""
    return bytes.fromhex(
        "AA133001822C6A050000015D02210100FE15626A7A6B776A6A6A6A4F6A6A6AEA"
        "420EFA6BC668DA6C6AB0676ADF7A6A6ADA28D77A6A6AAC288A7A6A827A6A9A7A"
        "0E927A6ABA7B6A827B6A9A7B6ABF4F6A6A6A6AF04D6D606F6A6A6A6A6AF85A"
        "69606B5ADA596BD25974A85969606B5AA25968BA5974B25968805969606B5AF25E"
        "68CA5E6BC25E6BDA5E6BD25E6BAA5E6BA25E6BBA5E6AB75E6A6A6A6A8F5E6A"
        "6A6A6A875E6A6A6A6A9F5E6A6A6A6A975E6A6A6A6AEA5F68E25F68FA5F6AC8"
        "5F65676A6A6AEA7F6A6A6AEA776A6A6AEAC05F65676A6A6AEA7F6A6A6AEA776A"
        "6A6AEAD85F65676A6A6AEA7F0C0CCCAA776A6A6AEAD05F65676A6A6AEA7F0C0C"
        "CCAA776A6A6AEAA85F65676A6A6AEA7F6A6A6AEA776A6A6AEAA05F65676A6A6A"
        "EA7F6A6A6AEA776A6A6AEAE22468FA2468B22495959595659A246A92246AAF0C6"
        "A6A6A6AECB7"
    )


@pytest.fixture
def device(mocker: MockerFixture):
    ble_dev = mocker.Mock()
    ble_dev.address = "B4:3A:45:9E:3B:72"
    adv_data = mocker.MagicMock()
    adv_data.manufacturer_data = {0xB5B5: b"\x00P521ZA1B3J3P0079"}
    return Device(ble_dev, adv_data, "P521ZA1B3J3P0079")


def test_rapid_pro_320_matches_serial_prefix():
    assert Device.check(b"P521ZA1B3J3P0079")
    assert not Device.check(b"R655TEST1234")


def test_rapid_pro_320_uses_prebound_local_auth_identity():
    assert Device.AUTH_USER_ID == "homeassistant"


async def test_rapid_pro_320_parses_captured_packet(device, display_packet):
    packet = await device.packet_parse(display_packet)

    assert not Packet.is_invalid(packet)
    assert (packet.src, packet.cmd_set, packet.cmd_id) == (0x02, 0xFE, 0x15)
    assert len(packet.payload) == 304
    assert await device.data_parse(packet) is True


async def test_rapid_pro_320_decodes_system_and_fault_telemetry(device, display_packet):
    packet = await device.packet_parse(display_packet)
    await device.data_parse(packet)

    assert device.battery_level == 88
    assert device.state_of_health == 99
    assert device.input_power == 0
    assert device.output_power == 0
    assert device.cell_temperature == 0
    assert device.device_error_codes == [0, 0, 0, 0, 0]
    assert device.error_occurred is False


async def test_rapid_pro_320_decodes_all_six_ports(device, display_packet):
    packet = await device.packet_parse(display_packet)
    await device.data_parse(packet)

    for name in ("usb_c1", "usb_c2", "usb_c3", "usb_c4", "usb_a1", "pogo"):
        assert isinstance(getattr(device, f"{name}_power"), float)
        assert isinstance(getattr(device, f"{name}_voltage"), float)
        assert isinstance(getattr(device, f"{name}_current"), float)
        assert getattr(device, f"{name}_port_enabled") is True

    assert device.usb_c4_voltage == -5.2
    assert device.usb_a1_voltage == -5.2
