/**
 * Copyright 2018 Google Inc. All Rights Reserved.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

'use strict';

const functions = require('firebase-functions');
const {smarthome} = require('actions-on-google');
const util = require('util');
const admin = require('firebase-admin');
const SERVER = "https://api.thingspeak.com";
// Initialize Firebase
admin.initializeApp();
const firebaseRef = admin.database().ref('/');

exports.fakeauth = functions.https.onRequest((request, response) => {
  const responseurl = util.format('%s?code=%s&state=%s',
    decodeURIComponent(request.query.redirect_uri), 'xxxxxx',
    request.query.state);
  console.log(responseurl);
  return response.redirect(responseurl);
});

exports.faketoken = functions.https.onRequest((request, response) => {
  const grantType = request.query.grant_type
    ? request.query.grant_type : request.body.grant_type;
  const secondsInDay = 86400; // 60 * 60 * 24
  const HTTP_STATUS_OK = 200;
  console.log(`Grant type ${grantType}`);

  let obj;
  if (grantType === 'authorization_code') {
    obj = {
      token_type: 'bearer',
      access_token: '123access',
      refresh_token: '123refresh',
      expires_in: secondsInDay,
    };
  } else if (grantType === 'refresh_token') {
    obj = {
      token_type: 'bearer',
      access_token: '123access',
      expires_in: secondsInDay,
    };
  }
  response.status(HTTP_STATUS_OK)
    .json(obj);
});
/*
let jwt;
try {
  jwt = require('./key.json');
} catch (e) {
  console.warn('Service account key is not found');
  console.warn('Report state will be unavailable');
}
*/
const app = smarthome({
  debug: true,
  key: '<api-key>',
  //jwt: jwt,
});

app.onSync((body) => {
  return {
    requestId: body.requestId,
    payload: {
      agentUserId: '123',
      devices: [{
        id: 'endpoint-001',
        type: 'action.devices.types.LUCE',
        traits: [
          'action.devices.traits.OnOff',
        ],
        name: {
          defaultNames: ['luce'],
          name: 'Luce',
          nicknames: ['Luce','Led'],
        },
        deviceInfo: {
          manufacturer: 'smartme',
          model: 'smartme-luce',
          hwVersion: '1.0',
          swVersion: '1.0.1',
        },
      }],
    },
  };
});

//lista canali e apikey per ogni appliance
const CHANNEL_ID = {
    "endpoint-001":
    {
        "channelId": "123456",
        "api_key":"XXXXXXXXXXXXXXX"

    }

}

const queryDatabase = (deviceId) => {

    channelId = CHANNEL_ID[deviceId]['channelId'];
    apikey = CHANNEL_ID[deviceId]['apikey'];
    var url=SERVER+"/channels/"+channelId+"/fields/1/last.json?api_key="+apikey;
    var xmlHttp = new XMLHttpRequest();
    xmlHttp.open( "GET", url, false ); // false for synchronous request
    xmlHttp.send( null );
    var r= JSON.parse(xmlHttp.responseText);
    if (r.field1 == 1){
      var value = true;
    }else {
      var value = false;
    }
  console.log(url);
  console.log(value);
    return {
      on: value,
    };
  };

const queryDevice = (deviceId) => queryDatabase(deviceId).then((data) => ({
  on: data.on,
}));

const updateDatabase = (deviceId,value) => {

      channelId = CHANNEL_ID[deviceId]['channelId'];
      apikey = CHANNEL_ID[deviceId]['apikey'];
      if (value == "ON")
        field="1";
      else
        field="0";
      var url=SERVER+"/update?api_key="+apikey+"&field1="+field;
      var xmlHttp = new XMLHttpRequest();
      xmlHttp.open( "GET", url, false ); // false for synchronous request
      xmlHttp.send( null );
      var r= xmlHttp.responseText;
    console.log(url);
    console.log(r);
    };



app.onQuery((body) => {
  console.log('onQuery');
  const {requestId} = body;
  const payload = {
    devices: {},
  };
  const queryPromises = [];
  for (const input of body.inputs) {
    for (const device of input.payload.devices) {
      const deviceId = device.id;
      queryPromises.push(queryDevice(deviceId)
        .then((data) => {
          // Add response to device payload
          payload.devices[deviceId] = data;
        }
        ));
    }
  }
  // Wait for all promises to resolve
  return Promise.all(queryPromises).then((values) => ({
    requestId: requestId,
    payload: payload,
  })
  );
});

app.onExecute((body) => {
  const {requestId} = body;
  const payload = {
    commands: [{
      ids: [],
      status: 'SUCCESS',
      states: {
        online: true,
      },
    }],
  };
  for (const input of body.inputs) {
    for (const command of input.payload.commands) {
      for (const device of command.devices) {
        const deviceId = device.id;
        payload.commands[0].ids.push(deviceId);
        for (const execution of command.execution) {
          const execCommand = execution.command;
          const {params} = execution;
          switch (execCommand) {
            case 'action.devices.commands.OnOff':
              //update thingspeak
              updateDatabase(deviceId,params.on);
              payload.commands[0].states.on = params.on;
              break;
            //aggiungere altre possibili azioni
          }
        }
      }
    }
  }
  return {
    requestId: requestId,
    payload: payload,
  };
});

exports.smarthome = functions.https.onRequest(app);

exports.requestsync = functions.https.onRequest((request, response) => {
  console.info('Request SYNC for user 123');
  app.requestSync('123')
    .then((res) => {
      console.log('Request sync completed');
      response.json(res.data);
    }).catch((err) => {
      console.error(err);
    });
});
