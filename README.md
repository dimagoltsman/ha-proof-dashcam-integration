# STILL IN DEV!

# ha-proof-dashcam-integration
HACS integration to proof.co.il dashcam

![Proof](https://github.com/dimagoltsman/ha-proof-dashcam-integration/blob/main/screenshot.png?raw=true)

If you cant find the integration in HACS, just add this repo as a custom one.

usage:

configuration.yaml:
```yaml
proof:
  audi:
    username: !secret proof_username
    password: !secret proof_password
    update_interval: 300
    name: "A 5"
```



# cards:

map:
Method 1: just add a map card with the entity
Method2: add custom code card:
```yaml
type: map
entities:
  - entity: proof.audi
default_zoom: 17
title: Audi A5
```

Picture from camera with refresh button: (make sure u also have my refreshable-picture-card for best results)
```yaml
cards:
  - entity_picture: proof.audi
    attribute: last_pic
    title: pic
    type: 'custom:refreshable-picture-card'
    update_interval: 1
  - hold_action:
      action: none
    name: Refresh
    show_icon: false
    show_name: true
    show_state: false
    tap_action:
      action: call-service
      service: proof.download_pic
      service_data:
        entity_id: audi
    type: button
type: vertical-stack
```

