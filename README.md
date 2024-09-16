
===========================================
JBL_Integration
===========================================


.. introduction-begin

This repository is a soundbars JBL_integration for a `Home Assistant`, this as a custom component

This integration is only usable if you're also able to use the 'JBL one' app (https://play.google.com/store/apps/details?id=com.jbl.oneapp). 

.. introduction-end



Usage
=====

.. usage-begin

It is recommended to use the latest stable version by using the command:

.. parsed-literal::

   $ cookiecutter gh:oncleben31/homeassistant-custom-component \\
     --checkout=\ |current-stable-version|\


.. usage-end

Features
========

.. features-begin

- Read state of the soundbar
- Setting Volume
- Simulate button presses
- Setting EQ
.. features-end

## Installation Instructions

### Using HACS

Not possible yet

### Manual install

1. Download the `custom_components/jbl_integration` directory to your Home Assistant configuration directory
2. Restart Home Assistant
3. Proceed to [Setup instructions](#setup-instructions)

## Setup Instructions

[![Open your Home Assistant instance and start setting up a new integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=jbl_integration)

1. Go to the Integrations page
2. Search for "jbl_integration"
3. Through the UI configure the ip address of the soundbar 
4. Wait a few seconds, and the integration should be ready.


