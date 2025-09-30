JBL_Integration
===========================================

This repository is a soundbars JBL_integration for a `Home Assistant`, this as a custom component.

This integration is only usable if you're also able to use the 'JBL one' app (https://play.google.com/store/apps/details?id=com.jbl.oneapp). 




Usage
=====


It is recommended to use the latest stable version by using the command:



Features
========
- Read state of the soundbar
- Setting Volume
- Simulate button presses
- Setting EQ

## Installation Instructions

### Using HACS

1. Add this repository as a custom repository in HACS. Either by manually adding `https://github.com/MrBearPresident/JBL_Soundbar` with category `integration` or simply click the following button:

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=MrBearPresident&repository=JBL_Soundbar&category=integration)

2. Search for "JBL_integration" in HACS and install the integration
3. Restart Home Assistant
4. Proceed to [Setup instructions](#setup-instructions)

### Manual install

1. Download the `custom_components/jbl_integration` directory to your Home Assistant configuration directory
2. Restart Home Assistant
3. Proceed to [Setup instructions](#setup-instructions)

## Setup Instructions

[![Open your Home Assistant instance and start setting up a new integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=jbl_integration)
### Automatic Setup
The integration will scann network devices through zeroconf and propose them to you. 

### Manual Setup
1. Go to the Integrations page
2. Search for "jbl_integration"
3. Through the UI, configure the ip address of the soundbar 
4. Wait a few seconds, and the integration should be ready.



#Working Models


| Firmware Version | 24.15.21.80.00 | 24.xx.31.80.00 |
| ------------- | ------------- |------------- |
| JBL Bar 300 | |Works With V1.2.0|
| JBL Bar 500 | | |
| JBL Bar 700 | | |
| JBL Bar 800 | Works With V1.1.1d |Works With V1.2.0 |
| JBL Bar 1000 |  Works With V1.1.1d |Works With V1.2.0 |
| JBL Bar 1300 | |Works With V1.2.0|
| JBL Bar 1300X | | |
