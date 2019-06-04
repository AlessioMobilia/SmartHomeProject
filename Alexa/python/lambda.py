# -*- coding: utf-8 -*-

# Copyright 2017 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Amazon Software License (the "License"). You may not use this file except in
# compliance with the License. A copy of the License is located at
#
#    http://aws.amazon.com/asl/
#
# or in the "license" file accompanying this file. This file is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, express or implied. See the License for the specific
# language governing permissions and limitations under the License.

"""Alexa Smart Home Lambda Function Sample Code.

This file demonstrates some key concepts when migrating an existing Smart Home skill Lambda to
v3, including recommendations on how to transfer endpoint/appliance objects, how v2 and vNext
handlers can be used together, and how to validate your v3 responses using the new Validation
Schema.

Note that this example does not deal with user authentication, only uses virtual devices, omits
a lot of implementation and error handling to keep the code simple and focused.
"""

import logging
import time
import json
import uuid
#import request for http request
from botocore.vendored import requests

# Imports for v3 validation
from validation import validate_message

# Setup logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# SERVER thingspeak connection
SERVER = "https://api.thingspeak.com"

# To simplify this sample Lambda, we omit validation of access tokens and retrieval of a specific
# user's appliances. Instead, this array includes a variety of virtual appliances in v2 API syntax,
# and will be used to demonstrate transformation between v2 appliances and v3 endpoints.
SAMPLE_APPLIANCES = [
    {
        "applianceId": "endpoint-001",
        "manufacturerName": "Sample Manufacturer",
        "modelName": "Smart Switch",
        "version": "1",
        "friendlyName": "esp",
        "friendlyDescription": "001 Switch that can only be turned on/off",
        "isReachable": True,
        "actions": [
            "turnOn",
            "turnOff",
            "ReportState"
        ],
        "additionalApplianceDetails": {
            "detail1": "For simplicity, this is the only appliance",
            "detail2": "that has some values in the additionalApplianceDetails"
        }
    }
]

#lista canali e apikey per ogni appliance
CHANNEL_ID = {
    "endpoint-001":
    {
        "channelId": "123456",
        "api_key":"XXXXXXXXXXXXXX"

    }

}



def lambda_handler(request, context):
    """Main Lambda handler.

    Since you can expect both v2 and v3 directives for a period of time during the migration
    and transition of your existing users, this main Lambda handler must be modified to support
    both v2 and v3 requests.
    """

    try:
        logger.info("Directive:")
        logger.info(json.dumps(request, indent=4, sort_keys=True))

        version = get_directive_version(request)

        if version == "3":
            logger.info("Received v3 directive!")
            if request["directive"]["header"]["name"] == "Discover":
                response = handle_discovery_v3(request)
            else:
                response = handle_non_discovery_v3(request)

        else:
            logger.info("Received v2 directive!")
            if request["header"]["namespace"] == "Alexa.ConnectedHome.Discovery":
                response = handle_discovery()
            else:
                response = handle_non_discovery(request)

        logger.info("Response:")
        logger.info(json.dumps(response, indent=4, sort_keys=True))

        #if version == "3":
            #logger.info("Validate v3 response")
            #validate_message(request, response)

        return response
    except ValueError as error:
        logger.error(error)
        raise

# v2 handlers
def handle_discovery():
    header = {
        "namespace": "Alexa.ConnectedHome.Discovery",
        "name": "DiscoverAppliancesResponse",
        "payloadVersion": "2",
        "messageId": get_uuid()
    }
    payload = {
        "discoveredAppliances": SAMPLE_APPLIANCES
    }
    response = {
        "header": header,
        "payload": payload
    }
    return response

def handle_non_discovery(request):
    request_name = request["header"]["name"]

    if request_name == "TurnOnRequest":
        header = {
            "namespace": "Alexa.ConnectedHome.Control",
            "name": "TurnOnConfirmation",
            "payloadVersion": "2",
            "messageId": get_uuid()
        }
        payload = {}
    elif request_name == "TurnOffRequest":
        header = {
            "namespace": "Alexa.ConnectedHome.Control",
            "name": "TurnOffConfirmation",
            "payloadVersion": "2",
            "messageId": get_uuid()
        }
    # other handlers omitted in this example
    payload = {}
    response = {
        "header": header,
        "payload": payload
    }
    return response

# v2 utility functions
def get_appliance_by_appliance_id(appliance_id):
    for appliance in SAMPLE_APPLIANCES:
        if appliance["applianceId"] == appliance_id:
            return appliance
    return None

def get_utc_timestamp(seconds=None):
    return time.strftime("%Y-%m-%dT%H:%M:%S.00Z", time.gmtime(seconds))

def get_uuid():
    return str(uuid.uuid4())

# v3 handlers
def handle_discovery_v3(request):
    endpoints = []
    for appliance in SAMPLE_APPLIANCES:
        endpoints.append(get_endpoint_from_v2_appliance(appliance))

    response = {
        "event": {
            "header": {
                "namespace": "Alexa.Discovery",
                "name": "Discover.Response",
                "payloadVersion": "3",
                "messageId": get_uuid()
            },
            "payload": {
                "endpoints": endpoints
            }
        }
    }
    return response

#accensione/spegnimento device
def handle_PoweSet(request,value):
    appliance = request["directive"]["endpoint"]["endpointId"]
    print("appliance="+appliance)
    channelId = CHANNEL_ID[appliance]["channelId"]
    apikey= CHANNEL_ID[appliance]["api_key"]
    if value == "ON":
        field="1"
    else :
        field="0"
    url=SERVER+"/update?api_key="+apikey+"&field1="+field
    # handler di accensione del dispositivo.
    r = requests.get(url)
    print("responso= "+r.text)
    if int(r.text) ==0 :
        value = "ERRORE"
    return value

def handle_ReportState(request):
    appliance = request["directive"]["endpoint"]["endpointId"]
    print("appliance="+appliance)
    channelId = CHANNEL_ID[appliance]["channelId"]
    apikey= CHANNEL_ID[appliance]["api_key"]

    #richiesta info dispositivo SERVER+"channels/"+CHANNELID+"/fields/1/last.json?api_key="+APIKEY;
    url=SERVER+"/channels/"+channelId+"/fields/1/last.json?api_key="+apikey;
    # handler di accensione del dispositivo.
    r = requests.get(url)
    print(url)
    r=json.loads(r.text)
    print(r)
    if int(r["field1"]) == 1 :
        value = "ON"
    else :
        value = "OFF"
    return value



def handle_non_discovery_v3(request):
    request_namespace = request["directive"]["header"]["namespace"]
    request_name = request["directive"]["header"]["name"]

    if request_namespace == "Alexa.PowerController":
        if request_name == "TurnOn":
            value = "ON"
            value = handle_PoweSet(request,value)

        else:
            value = "OFF"
            value = handle_PoweSet(request,value)

        response = {
            "context": {
                "properties": [
                    {
                        "namespace": "Alexa.PowerController",
                        "name": "powerState",
                        "value": value,
                        "timeOfSample": get_utc_timestamp(),
                        "uncertaintyInMilliseconds": 500
                    }
                ]
            },
            "event": {
                "header": {
                    "namespace": "Alexa",
                    "name": "Response",
                    "payloadVersion": "3",
                    "messageId": get_uuid(),
                    "correlationToken": request["directive"]["header"]["correlationToken"]
                },
                "endpoint": {
                    "scope": {
                        "type": "BearerToken",
                        "token": "access-token-from-Amazon"
                    },
                    "endpointId": request["directive"]["endpoint"]["endpointId"]
                },
                "payload": {}
            }
        }
        return response

    elif request_namespace == "Alexa.Authorization":
        if request_name == "AcceptGrant":
            response = {
                "event": {
                    "header": {
                        "namespace": "Alexa.Authorization",
                        "name": "AcceptGrant.Response",
                        "payloadVersion": "3",
                        "messageId": "5f8a426e-01e4-4cc9-8b79-65f8bd0fd8a4"
                    },
                    "payload": {}
                }
            }
            return response
    elif request_namespace == "Alexa":
        if request_name == "ReportState":
            print("REPORT STATE")

            value=handle_ReportState(request)


            response = {
                "event": {
                    "header": {
                        "messageId": get_uuid(),
                        "correlationToken": request["directive"]["header"]["correlationToken"],
                        "namespace": "Alexa",
                        "name": "StateReport",
                        "payloadVersion": "3"
                    },
                    "endpoint": {
                        "scope": {
                            "type": "BearerToken",
                            "token": "access-token-from-Amazon"
                        },
                        "endpointId": request["directive"]["endpoint"]["endpointId"],
                    },
                    "payload": {}
                },
                "context": {
                    "properties": [
                    {
                        "namespace": "Alexa.PowerController",
                        "name": "powerState",
                        "value": value,
                        "timeOfSample": get_utc_timestamp(),
                        "uncertaintyInMilliseconds": 500
                    }
                ]
                }
            }


            return response
    # other handlers omitted in this example

# v3 utility functions
def get_endpoint_from_v2_appliance(appliance):
    endpoint = {
        "endpointId": appliance["applianceId"],
        "manufacturerName": appliance["manufacturerName"],
        "friendlyName": appliance["friendlyName"],
        "description": appliance["friendlyDescription"],
        "displayCategories": [],
        "cookie": appliance["additionalApplianceDetails"],
        "capabilities": []
    }
    endpoint["displayCategories"] = get_display_categories_from_v2_appliance(appliance)
    endpoint["capabilities"] = get_capabilities_from_v2_appliance(appliance)
    return endpoint

def get_directive_version(request):
    try:
        return request["directive"]["header"]["payloadVersion"]
    except:
        try:
            return request["header"]["payloadVersion"]
        except:
            return "-1"

def get_endpoint_by_endpoint_id(endpoint_id):
    appliance = get_appliance_by_appliance_id(endpoint_id)
    if appliance:
        return get_endpoint_from_v2_appliance(appliance)
    return None

def get_display_categories_from_v2_appliance(appliance):
    model_name = appliance["modelName"]
    if model_name == "Smart Switch": displayCategories = ["SWITCH"]
    elif model_name == "Smart Light": displayCategories = ["LIGHT"]
    elif model_name == "Smart White Light": displayCategories = ["LIGHT"]
    elif model_name == "Smart Thermostat": displayCategories = ["THERMOSTAT"]
    elif model_name == "Smart Lock": displayCategories = ["SMARTLOCK"]
    elif model_name == "Smart Scene": displayCategories = ["SCENE_TRIGGER"]
    elif model_name == "Smart Activity": displayCategories = ["ACTIVITY_TRIGGER"]
    elif model_name == "Smart Camera": displayCategories = ["CAMERA"]
    else: displayCategories = ["OTHER"]
    return displayCategories

def get_capabilities_from_v2_appliance(appliance):
    model_name = appliance["modelName"]
    if model_name == 'Smart Switch':
        capabilities = [
            {
                "type": "AlexaInterface",
                "interface": "Alexa.PowerController",
                "version": "3",
                "properties": {
                    "supported": [
                        { "name": "powerState" }
                    ],
                    "proactivelyReported": True,
                    "retrievable": True
                }
            },
            {
                "type": "AlexaInterface",
                "interface": "Alexa",
                "version": "3",
                "properties": {
                    "supported": [
                        { "name": "StateReport" }
                    ],
                    "proactivelyReported": True,
                    "retrievable": True
                }
            }
        ]
    elif model_name == "Smart Light":
        capabilities = [
            {
                "type": "AlexaInterface",
                "interface": "Alexa.PowerController",
                "version": "3",
                "properties": {
                    "supported": [
                        { "name": "powerState" }
                    ],
                    "proactivelyReported": True,
                    "retrievable": True
                }
            },
            {
                "type": "AlexaInterface",
                "interface": "Alexa.ColorController",
                "version": "3",
                "properties": {
                    "supported": [
                        { "name": "color" }
                    ],
                    "proactivelyReported": True,
                    "retrievable": True
                }
            },
            {
                "type": "AlexaInterface",
                "interface": "Alexa.ColorTemperatureController",
                "version": "3",
                "properties": {
                    "supported": [
                        { "name": "colorTemperatureInKelvin" }
                    ],
                    "proactivelyReported": True,
                    "retrievable": True
                }
            },
            {
                "type": "AlexaInterface",
                "interface": "Alexa.BrightnessController",
                "version": "3",
                "properties": {
                    "supported": [
                        { "name": "brightness" }
                    ],
                    "proactivelyReported": True,
                    "retrievable": True
                }
            },
            {
                "type": "AlexaInterface",
                "interface": "Alexa.PowerLevelController",
                "version": "3",
                "properties": {
                    "supported": [
                        { "name": "powerLevel" }
                    ],
                    "proactivelyReported": True,
                    "retrievable": True
                }
            },
            {
                "type": "AlexaInterface",
                "interface": "Alexa.PercentageController",
                "version": "3",
                "properties": {
                    "supported": [
                        { "name": "percentage" }
                    ],
                    "proactivelyReported": True,
                    "retrievable": True
                }
            }
        ]
    elif model_name == "Smart White Light":
        capabilities = [
            {
                "type": "AlexaInterface",
                "interface": "Alexa.PowerController",
                "version": "3",
                "properties": {
                    "supported": [
                        { "name": "powerState" }
                    ],
                    "proactivelyReported": True,
                    "retrievable": True
                }
            },
            {
                "type": "AlexaInterface",
                "interface": "Alexa.ColorTemperatureController",
                "version": "3",
                "properties": {
                    "supported": [
                        { "name": "colorTemperatureInKelvin" }
                    ],
                    "proactivelyReported": True,
                    "retrievable": True
                }
            },
            {
                "type": "AlexaInterface",
                "interface": "Alexa.BrightnessController",
                "version": "3",
                "properties": {
                    "supported": [
                        { "name": "brightness" }
                    ],
                    "proactivelyReported": True,
                    "retrievable": True
                }
            },
            {
                "type": "AlexaInterface",
                "interface": "Alexa.PowerLevelController",
                "version": "3",
                "properties": {
                    "supported": [
                        { "name": "powerLevel" }
                    ],
                    "proactivelyReported": True,
                    "retrievable": True
                }
            },
            {
                "type": "AlexaInterface",
                "interface": "Alexa.PercentageController",
                "version": "3",
                "properties": {
                    "supported": [
                        { "name": "percentage" }
                    ],
                    "proactivelyReported": True,
                    "retrievable": True
                }
            }
        ]
    elif model_name == "Smart Thermostat":
        capabilities = [
            {
                "type": "AlexaInterface",
                "interface": "Alexa.ThermostatController",
                "version": "3",
                "properties": {
                    "supported": [
                        { "name": "targetSetpoint" },
                        { "name": "thermostatMode" }
                    ],
                    "proactivelyReported": True,
                    "retrievable": True
                }
            },
            {
                "type": "AlexaInterface",
                "interface": "Alexa.TemperatureSensor",
                "version": "3",
                "properties": {
                    "supported": [
                        { "name": "temperature" }
                    ],
                    "proactivelyReported": True,
                    "retrievable": True
                }
            }
        ]
    elif model_name == "Smart Thermostat Dual":
        capabilities = [
            {
                "type": "AlexaInterface",
                "interface": "Alexa.ThermostatController",
                "version": "3",
                "properties": {
                    "supported": [
                        { "name": "upperSetpoint" },
                        { "name": "lowerSetpoint" },
                        { "name": "thermostatMode" }
                    ],
                    "proactivelyReported": True,
                    "retrievable": True
                }
            },
            {
                "type": "AlexaInterface",
                "interface": "Alexa.TemperatureSensor",
                "version": "3",
                "properties": {
                    "supported": [
                        { "name": "temperature" }
                    ],
                    "proactivelyReported": True,
                    "retrievable": True
                }
            }
        ]
    elif model_name == "Smart Lock":
        capabilities = [
            {
                "type": "AlexaInterface",
                "interface": "Alexa.LockController",
                "version": "3",
                "properties": {
                    "supported": [
                        { "name": "lockState" }
                    ],
                    "proactivelyReported": True,
                    "retrievable": True
                }
            }
        ]
    elif model_name == "Smart Scene":
        capabilities = [
            {
                "type": "AlexaInterface",
                "interface": "Alexa.SceneController",
                "version": "3",
                "supportsDeactivation": False,
                "proactivelyReported": True
            }
        ]
    elif model_name == "Smart Activity":
        capabilities = [
            {
                "type": "AlexaInterface",
                "interface": "Alexa.SceneController",
                "version": "3",
                "supportsDeactivation": True,
                "proactivelyReported": True
            }
        ]
    elif model_name == "Smart Camera":
        capabilities = [
            {
                "type": "AlexaInterface",
                "interface": "Alexa.CameraStreamController",
                "version": "3",
                "cameraStreamConfigurations" : [ {
                    "protocols": ["RTSP"],
                    "resolutions": [{"width":1280, "height":720}],
                    "authorizationTypes": ["NONE"],
                    "videoCodecs": ["H264"],
                    "audioCodecs": ["AAC"]
                } ]
            }
        ]
    else:
        # in this example, just return simple on/off capability
        capabilities = [
            {
                "type": "AlexaInterface",
                "interface": "Alexa.PowerController",
                "version": "3",
                "properties": {
                    "supported": [
                        { "name": "powerState" }
                    ],
                    "proactivelyReported": True,
                    "retrievable": True
                }
            }
        ]

    # additional capabilities that are required for each endpoint
    endpoint_health_capability = {
        "type": "AlexaInterface",
        "interface": "Alexa.EndpointHealth",
        "version": "3",
        "properties": {
            "supported":[
                { "name":"connectivity" }
            ],
            "proactivelyReported": True,
            "retrievable": True
        }
    }
    alexa_interface_capability = {
        "type": "AlexaInterface",
        "interface": "Alexa",
        "version": "3"
    }
    capabilities.append(endpoint_health_capability)
    capabilities.append(alexa_interface_capability)
    return capabilities
