"""Tests for capture device listing and resolve fallbacks."""
from audio_devices import CaptureDevice, list_capture_devices, resolve_device, source_choices


class FakePa:
    def __init__(self, loopbacks=None, inputs=None):
        self._loopbacks = loopbacks or []
        self._inputs = inputs or []
        self.default_loopback = {'index': 90, 'name': 'Default Loopback', 'maxInputChannels': 2}
        self.default_input = {'index': 91, 'name': 'Default Mic', 'maxInputChannels': 1}

    def get_loopback_device_info_generator(self):
        yield from self._loopbacks

    def get_device_info_generator(self):
        yield from self._inputs

    def get_device_info_by_index(self, index):
        for device in self._loopbacks + self._inputs:
            if device['index'] == index:
                return device
        raise IOError(index)

    def get_default_wasapi_loopback(self):
        return self.default_loopback

    def get_default_input_device_info(self):
        return self.default_input


def test_list_capture_devices_includes_loopback_and_input():
    pa = FakePa(
        loopbacks=[{
            'index': 1, 'name': 'Speakers [Loopback]', 'maxInputChannels': 2,
            'defaultSampleRate': 48000, 'isLoopbackDevice': True,
        }],
        inputs=[{
            'index': 2, 'name': 'Voicemeeter Out B1', 'maxInputChannels': 2,
            'defaultSampleRate': 48000, 'isLoopbackDevice': False,
        }, {
            'index': 3, 'name': 'Silent', 'maxInputChannels': 0,
            'defaultSampleRate': 48000, 'isLoopbackDevice': False,
        }],
    )
    devices = list_capture_devices(pa)
    assert [d.name for d in devices] == ['Speakers [Loopback]', 'Voicemeeter Out B1']
    assert devices[0].kind == 'loopback'
    assert devices[1].kind == 'input'


def test_resolve_device_by_exact_name():
    target = {
        'index': 5, 'name': 'Voicemeeter Aux Input', 'maxInputChannels': 2,
        'defaultSampleRate': 48000, 'isLoopbackDevice': False,
    }
    pa = FakePa(inputs=[target])
    device = resolve_device(pa, {'source': 'device', 'device_name': 'Voicemeeter Aux Input'})
    assert device['index'] == 5


def test_resolve_device_falls_back_when_missing():
    pa = FakePa()
    device = resolve_device(pa, {'source': 'device', 'device_name': 'Missing Cable'})
    assert device['name'] == 'Default Loopback'


def test_resolve_system_and_microphone():
    pa = FakePa()
    assert resolve_device(pa, {'source': 'system'})['name'] == 'Default Loopback'
    assert resolve_device(pa, {'source': 'microphone'})['name'] == 'Default Mic'


def test_source_choices_include_devices():
    devices = [CaptureDevice(1, 'Cable A', 'loopback', 2, 48000.0)]
    choices = source_choices(devices)
    assert choices[0][:2] == ('Systeemaudio (WASAPI)', 'system')
    assert choices[-1] == ('Loopback: Cable A', 'device', 'Cable A')
