# miio Five UV Light

This is a custom component for Home Assistant to integrate the Five UV Light.

Please follow the instructions on [Retrieving the Access Token](https://home-assistant.io/components/xiaomi/#retrieving-the-access-token) to get the API token to use in the configuration.yaml file.

Credits: Thanks to [Rytilahti](https://github.com/rytilahti/python-miio) for all the work.

## Features

### Five UV Light

Supported models: `uvfive.s_lamp.slmap2`.

* Power (on, off)
* Child Lock (on, off)
* Disable Radar (on, off)
* Setting Sterilization Time (5...45 minutes)
* Attributes
  - Sterilization Time
  - Stop Countdown
  - Child Lock
  - Disable Radar
  - UV Status (off, starting, sterilizing)
  - model

# Install
You can install it manually by copying the custom_component folder to your Home Assistant configuration folder.

# Setup

```
# configuration.yaml

light:
  - platform: five_uv
    name: Five UV Light
    host: 192.168.1.59
    token: 7edd024793d8505e9937d625fd7dae86
```

Configuration variables:
- **name** (*Optional*): The name of your light.
- **host** (*Required*): The IP of your light.
- **token** (*Required*): The API token of your light.

## Platform services

#### Service `five_uv.set_child_lock__on`

Turn the child lock on.

| Service data attribute    | Optional | Description                                             |
|---------------------------|----------|---------------------------------------------------------|
| `entity_id`               |       no | Name of the five uv light entity.                       |

#### Service `five_uv.set_child_lock__off`

Turn the child lock off.

| Service data attribute    | Optional | Description                                             |
|---------------------------|----------|---------------------------------------------------------|
| `entity_id`               |       no | Name of the five uv light entity.                       |

#### Service `five_uv.set_disable_radar_on`

Turn the disable radar on.

| Service data attribute    | Optional | Description                                             |
|---------------------------|----------|---------------------------------------------------------|
| `entity_id`               |       no | Name of the five uv light entity.                       |

#### Service `five_uv.set_disable_radar_off`

Turn the disable radar off.

| Service data attribute    | Optional | Description                                             |
|---------------------------|----------|---------------------------------------------------------|
| `entity_id`               |       no | Name of the five uv light entity.                       |

#### Service `five_uv.set_sterilization_time`

Set the sterilization time.

| Service data attribute    | Optional | Description                                             |
|---------------------------|----------|---------------------------------------------------------|
| `entity_id`               |       no | Name of the five uv light entity.                       |
| `minutes`                 |       no | Sterilization time, between 5 and 45.                   |
