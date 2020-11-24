"""Support for FIVE UV Light by miio."""
import asyncio
from functools import partial
import logging

from miio import (  # pylint: disable=import-error
    Device,
    DeviceException,
)
import voluptuous as vol

from homeassistant.components.light import PLATFORM_SCHEMA, LightEntity
from homeassistant.const import (
    ATTR_ENTITY_ID,
    CONF_HOST,
    CONF_NAME,
    CONF_TOKEN,
)
from homeassistant.exceptions import PlatformNotReady
import homeassistant.helpers.config_validation as cv

_LOGGER = logging.getLogger(__name__)

DEFAULT_NAME = "Five UV light"
DATA_KEY = "light.five_uv_light"
DOMAIN = "five_uv"

CONF_MODEL = "model"

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_HOST): cv.string,
        vol.Required(CONF_TOKEN): vol.All(cv.string, vol.Length(min=32, max=32)),
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
        vol.Optional(CONF_MODEL): vol.In(
            [
                "uvfive.s_lamp.slmap2",
            ]
        ),
    }
)

ATTR_SIID_21 = 'siid_21'
ATTR_UV_STATUS = 'uv_status'
ATTR_STERILIZATION_TIME = 'sterilization_time'
ATTR_STOP_COUNTDOWN = 'stop_countdown'
ATTR_CHILD_LOCK = 'child_lock'
ATTR_DISABLE_RADAR = 'Disable_radar'
ATTR_MODEL = "model"
ATTR_MINUTES = 'minutes'

SUCCESS = ["ok"]

SERVICE_SET_STERILIZATION_TIME = "set_sterilization_time"
SERVICE_SET_CHILD_LOCK_ON = "set_child_lock_on"
SERVICE_SET_CHILD_LOCK_OFF = "set_child_lock_off"
SERVICE_SET_DISABLE_RADAR_ON = "set_disable_radar_on"
SERVICE_SET_DISABLE_RADAR_OFF = "set_disable_radar_off"

SERVICE_SCHEMA = vol.Schema({vol.Optional(ATTR_ENTITY_ID): cv.entity_ids})

SERVICE_SCHEMA_STERILIZATION_TIME = SERVICE_SCHEMA.extend(
    {vol.Required(ATTR_MINUTES, default=30): vol.All(int, vol.Range(min=5, max=45))}
)

SERVICE_TO_METHOD = {
    SERVICE_SET_STERILIZATION_TIME: {
        'method': 'async_set_sterilization_time',
        'schema': SERVICE_SCHEMA_STERILIZATION_TIME,
    },
    SERVICE_SET_CHILD_LOCK_ON: {'method': "async_set_child_lock_on"},
    SERVICE_SET_CHILD_LOCK_OFF: {'method': "async_set_child_lock_off"},
    SERVICE_SET_DISABLE_RADAR_ON: {'method': "async_set_disable_radar_on"},
    SERVICE_SET_DISABLE_RADAR_OFF: {'method': "async_set_disable_radar_off"},
}

async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the switch from config."""
    if DATA_KEY not in hass.data:
        hass.data[DATA_KEY] = {}

    host = config[CONF_HOST]
    token = config[CONF_TOKEN]
    name = config[CONF_NAME]
    model = config.get(CONF_MODEL)

    _LOGGER.info("Initializing with host %s (token %s...)", host, token[:5])

    devices = []
    unique_id = None

    if model is None:
        try:
            miio_device = Device(host, token)
            device_info = await hass.async_add_executor_job(miio_device.info)
            model = device_info.model
            unique_id = f"{model}-{device_info.mac_address}-five_uv"
            _LOGGER.info(
                "%s %s %s detected",
                model,
                device_info.firmware_version,
                device_info.hardware_version,
            )
        except DeviceException as ex:
            raise PlatformNotReady from ex

    if model in ["uvfive.s_lamp.slmap2"]:
        uv_device = Device(host, token)
        device = Five_UV_Light(name, uv_device, model, unique_id)
        devices.append(device)
        hass.data[DATA_KEY][host] = device

    else:
        _LOGGER.error(
            "Unsupported device found! Please create an issue at "
            "https://github.com/vaughan-zeng/five_uv/issues "
            "and provide the following data: %s",
            model,
        )
        return False

    async_add_entities(devices, update_before_add=True)


    async def async_service_handler(service):
        """Map services to methods on Five_UV_Light."""
        method = SERVICE_TO_METHOD.get(service.service)
        params = {
            key: value for key, value in service.data.items() if key != ATTR_ENTITY_ID
        }
        entity_ids = service.data.get(ATTR_ENTITY_ID)
        if entity_ids:
            devices = [
                device
                for device in hass.data[DATA_KEY].values()
                if device.entity_id in entity_ids
            ]
        else:
            devices = hass.data[DATA_KEY].values()

        update_tasks = []
        for device in devices:
            if not hasattr(device, method["method"]):
                continue
            await getattr(device, method["method"])(**params)
            update_tasks.append(device.async_update_ha_state(True))

        if update_tasks:
            await asyncio.wait(update_tasks)

    for five_uv_service in SERVICE_TO_METHOD:
        schema = SERVICE_TO_METHOD[five_uv_service].get("schema", SERVICE_SCHEMA)
        hass.services.async_register(
            DOMAIN, five_uv_service, async_service_handler, schema=schema
        )


class Five_UV_Light(LightEntity):
    """Representation of Five UV Light."""

    def __init__(self, name, uv_device, model, unique_id):
        """Initialize the Five UV Light."""
        self._name = name
        self._uv_device = uv_device
        self._model = model
        self._unique_id = unique_id
        self._icon = 'mdi:lightbulb-cfl'
        self._available = False
        self._state = None
        self._state_attrs = {
            ATTR_STERILIZATION_TIME: None,
            ATTR_STOP_COUNTDOWN: None,
            ATTR_CHILD_LOCK: None,
            ATTR_DISABLE_RADAR: None,
            ATTR_SIID_21: None,
            ATTR_UV_STATUS: None,
            ATTR_MODEL: self._model}

        self._skip_update = False


    @property
    def unique_id(self):
        """Return an unique ID."""
        return self._unique_id

    @property
    def name(self):
        """Return the name of the device if any."""
        return self._name

    @property
    def icon(self):
        """Return the icon to use for device if any."""
        return self._icon

    @property
    def available(self):
        """Return true when state is known."""
        return self._available

    @property
    def device_state_attributes(self):
        """Return the state attributes of the device."""
        return self._state_attrs

    @property
    def is_on(self):
        """Return true if switch is on."""
        return self._state

    async def _try_command(self, mask_error, func, *args, **kwargs):
        """Call a device command handling error messages."""
        try:
            result = await self.hass.async_add_executor_job(partial(func, *args, **kwargs))
            _LOGGER.debug("Response received from five uv light: %s", result)
            return result == SUCCESS
        except DeviceException as exc:
            if self._available:
                _LOGGER.error(mask_error, exc)
                self._available = False
            return False

    async def async_turn_on(self, **kwargs):
        """Turn the five UV light on."""
        result = await self._try_command(
            "Turning the five UV light on failed.", 
            self._uv_device.send,
            'set_properties',
            [{"siid":2,"piid":2,"value":True}]
        )

        if result:
            self._state = True
            self._skip_update = True

    async def async_turn_off(self, **kwargs):
        """Turn the five UV light off."""
        result = await self._try_command(
            "Turning the five UV light off failed.",
            self._uv_device.send,
            'set_properties',
            [{"siid":2,"piid":2,"value":False}]
        )

        if result:
            self._state = False
            self._skip_update = True

    async def async_update(self):
        """Fetch state from the device."""
        # On state change the device doesn't provide the new state immediately.
        if self._skip_update:
            self._skip_update = False
            return

        try:
            state = await self.hass.async_add_executor_job(
                self._uv_device.send,
                'get_properties',
                [{"siid":2,"piid":1},
                {"siid":2,"piid":2},
                {"siid":2,"piid":3},
                {"siid":2,"piid":6},
                {"siid":2,"piid":7},
                {"siid":4,"piid":1},
                {"siid":5,"piid":1}]
            )
            _LOGGER.debug("Got the five UV light new state: %s", state)

            self._available = True

            self._state = state[1]['value']

            self._state_attrs[ATTR_SIID_21] = state[0]['value']

            status_value = state[2]['value']
            if status_value == 1:
                status = 'off'
            elif status_value == 3:
                status = 'starting'
            elif status_value == 4:
                status = 'sterilizing'
            self._state_attrs[ATTR_UV_STATUS] = status

            self._state_attrs[ATTR_STERILIZATION_TIME] = state[3]['value']
            self._state_attrs[ATTR_STOP_COUNTDOWN] = state[4]['value']
            self._state_attrs[ATTR_CHILD_LOCK] = state[5]['value']
            self._state_attrs[ATTR_DISABLE_RADAR] = state[6]['value']

        except DeviceException as ex:
            if self._available:
                self._available = False
                _LOGGER.error("Got exception while fetching the state: %s", ex)

    async def async_set_sterilization_time(self, minutes: int):
        """Set the UV sterilization time."""
        await self._try_command(
            "Setting the UV sterilization time failed.",
            self._uv_device.send,
            'set_properties',
            [{"siid":2,"piid":6,"value":minutes}]
        )

    async def async_set_child_lock_on(self):
        """Turn the child lock on."""
        await self._try_command(
            "Turning the child lock on failed.",
            self._uv_device.send,
            'set_properties',
            [{"siid":4,"piid":1,"value":True}]
        )

    async def async_set_child_lock_off(self):
        """Turn the child lock off."""
        await self._try_command(
            "Turning the child lock off failed.",
            self._uv_device.send,
            'set_properties',
            [{"siid":4,"piid":1,"value":False}]
        )

    async def async_set_disable_radar_on(self):
        """Turn the disable radar on."""
        await self._try_command(
            "Turning the disable radar on failed.",
            self._uv_device.send,
            'set_properties',
            [{"siid":5,"piid":1,"value":True}]
        )

    async def async_set_disable_radar_off(self):
        """Turn the disable radar off."""
        await self._try_command(
            "Turning the disable radar off failed.",
            self._uv_device.send,
            'set_properties',
            [{"siid":5,"piid":1,"value":False}]
        )
