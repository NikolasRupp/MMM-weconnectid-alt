try:
  import json
  import random
  import re
  import requests
  import string
  from sys import argv
  from datetime import datetime, timezone
  import time
except ModuleNotFoundError as e:
  output = {
    "status": 0,
    "error": str(e).replace("'","") + '. Please install it via Pip',
  }
  print(output)
  exit()

BASE_URL = 'https://mobileapi.apps.emea.vwapps.io'

class WeConnectId:
    def __init__(self, email_address, password, access_token=None):
        self._email_address = email_address
        self._password = password
        self._access_token = access_token

        self._setup_session()
        self._sign_in()

    def _setup_session(self):
        self._session = requests.session()

        self._session.headers.update({
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.45 Safari/537.36',
        })

    def _sign_in(self, force=False):
        if self._access_token is None or force:
            nonce = ''.join(random.choices(string.ascii_uppercase + string.ascii_lowercase + string.digits, k=16))

            r = self._session.get('https://login.apps.emea.vwapps.io/authorize?nonce=' + nonce + '&redirect_uri=weconnect://authenticated')

            # Enter e-mail address
            post_data = {
                '_csrf': re.search('name="_csrf" value="([^"]+)"', r.text).group(1),
                'relayState': re.search('name="relayState" value="([^"]+)"', r.text).group(1),
                'hmac': re.search('name="hmac" value="([^"]+)"', r.text).group(1),
                'email': self._email_address,
            }

            uuid = re.search('action="/signin-service/v1/([^@]+)@apps_vw-dilab_com/login/identifier"', r.text).group(1)

            r = self._session.post(
                'https://identity.vwgroup.io/signin-service/v1/' + uuid + '@apps_vw-dilab_com/login/identifier',
                data=post_data
            )

            some_data = json.loads(re.search('templateModel: ({.*}),', r.text).group(1))

            # Enter password
            post_data = {
                '_csrf': re.search('csrf_token: \'([^\']+)\'', r.text).group(1),
                'relayState': some_data['relayState'],
                'hmac': some_data['hmac'],
                'email': self._email_address,
                'password': self._password,
            }

            access_token = None

            try:
                r = self._session.post(
                    'https://identity.vwgroup.io/signin-service/v1/' + some_data['clientLegalEntityModel']['clientId'] + '/login/authenticate',
                    data=post_data
                )

            except requests.exceptions.InvalidSchema as e:
                # We expect a redirect to 'weconnect://authenticated', which requests doesn't understand
                self._access_token = re.search('access_token=([^&$]+)', str(e)).group(1)

        try:
          self._session.headers.update({
              'Authorization': 'Bearer ' + self._access_token,
          })
        except TypeError as e:
          output = {
            "status": 0,
            "error": "Invalid E-Mail or Password",
          }
          print(output)
          exit()

    def get_access_token(self):
        return self._access_token

    def get(self, endpoint):
        r = self._session.get(BASE_URL + endpoint)

        if r.status_code == 401:
            self._sign_in(True)

            r = self._session.get(BASE_URL + endpoint)

        return r.json()

found_vehicles = ""
vehicle = None
email_address = argv[1]
password = argv[2]
w = WeConnectId(email_address, password)
vehicles = w.get('/vehicles')

# print('list of vehicles:')
# pprint.pprint(vehicles)
# #
# print('\n---\n\n')
# #
# print('specific vehicle:')
# pprint.pprint(w.get('/vehicles/' + vehicles['data'][0]['vin'] + '/selectivestatus?jobs=all'))

for i in range (0,len(vehicles['data'])):
  if vehicles['data'][i]['vin'] == argv[3]:
    if vehicles["data"][i]["role"] == "GUEST_USER":
      output = {
        "status": 0,
        "error": f"Must be Main User not Guest User",
      }
      print(output)
      exit()
    else:
      vehicle = w.get(f'/vehicles/{argv[3]}/selectivestatus?jobs=all')
      model = vehicles["data"][i]["model"]
  else:
    found_vehicles += f" {vehicles['data'][i]['vin']}"


if vehicle is None:
  output = {
    "status": 0,
    "error": f"Invalid VIN. Found{found_vehicles}",
  }
  print(output)
  exit()

fields = {"bonnetDoor":["access","accessStatus","value","doors",0,"status",0],
          "trunkDoor":["access","accessStatus","value","doors",1,"status",0],
          "rearRightDoor":["access","accessStatus","value","doors",2,"status",0],
          "rearLeftDoor":["access","accessStatus","value","doors",3,"status",0],
          "frontRightDoor":["access","accessStatus","value","doors",4,"status",0],
          "frontLeftDoor":["access","accessStatus","value","doors",5,"status",0],
          "rearRightWindow":["access","accessStatus","value","windows",3,"status",0],
          "rearLeftWindow":["access","accessStatus","value","windows",4,"status",0],
          "frontRightWindow":["access","accessStatus","value","windows",5,"status",0],
          "frontLeftWindow":["access","accessStatus","value","windows",6,"status",0],
          "overallStatus":["access","accessStatus","value","overallStatus"],
          "rightLight":["vehicleLights","lightsStatus","value","lights",0,"status"],
          "leftLight":["vehicleLights","lightsStatus","value","lights",1,"status"],
          "remainingKm": ["charging","batteryStatus","value","cruisingRangeElectric_km"],
          "remainingSoC": ["charging","batteryStatus","value","currentSOC_pct"],
          "remainingChargingTime": ["charging","chargingStatus","value","remainingChargingTimeToComplete_min"],
          "chargingState": ["charging","chargingStatus","value","chargingState"],
          "chargePower": ["charging","chargingStatus","value","chargePower_kW"],
          "targetSoC": ["charging","chargingSettings","value","targetSOC_pct"],
          "kmph": ["charging","chargingStatus","value","chargeRate_kmph"],
          "odometer": ["measurements","odometerStatus","value","odometer"],
          "climatisation":["climatisation","climatisationStatus","value","climatisationState"],
          "temperature": ["climatisation","climatisationSettings","value","targetTemperature_C"],
}

try:
  timestamp = 0
  for key1 in vehicle.keys():
    try:
      for key2 in vehicle[key1].keys():
        if "carCapturedTimestamp" in vehicle[key1][key2]["value"].keys():
          temp_timestamp = datetime.timestamp(datetime.strptime(vehicle[key1][key2]["value"]["carCapturedTimestamp"], '%Y-%m-%dT%H:%M:%S.%fZ'))
          if temp_timestamp > timestamp:
            timestamp = temp_timestamp
    except:
      pass
  timestamp = datetime.fromtimestamp(timestamp).replace(tzinfo=timezone.utc).astimezone(tz=None).strftime("%d.%m.%Y %H:%M")

  output = {}
  for key in fields.keys():
    value = vehicle
    for field in fields.get(key):
      try:
        value = value[field]
      except:
        value = 0
        break
    output[key] = value
  output["timestamp"] = f'{timestamp} - ({datetime.now().strftime("%H:%M")})'
  output["model"] = model
  output["remainingChargingTime"] = time.strftime("%H:%M", time.gmtime(output.get("remainingChargingTime",0) * 60))
  output["odometer"] = f'{output.get("odometer",0):,}'.replace(",", ".")
  output["status"] = 1
  output["error"] = ""
  print(output)
  exit()
except Exception as e:
  output = {
    "status": 0,
    "error": str(e).replace("'",""),
  }
  print(output)
  exit()


