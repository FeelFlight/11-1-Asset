import os
import json
import time
import random
import couchdb
import threading
from   queue            import Queue
import paho.mqtt.client as     mqtt


class Asset(threading.Thread):

    def _getDBTemplate(self, type, id):
        r = {'_id': id}

        if "blouse" == type:
            pass

        if "blanket" == type:
            pass

        if "shoe" == type:
            pass

        return r

    def _setAssetLastSeen(self, type, id):
        try:
            db = self._couch[type]

            if id in db:
                d = db[id]
            else:
                d = self._getDBTemplate(type, id)

            d['lastseen'] = time.time()
            db.save(d)
        except Exception as e:
            print(e)

    def _setAssetBatteryLevel(self, type, id, level):
        try:
            l = float(level) / 1000.0
            db = self._couch[type]

            if id in db:
                d = db[id]
            else:
                d = self._getDBTemplate(type, id)

            d['batterylevel'] = l
            d['lastseen']     = time.time()
            db.save(d)
        except Exception as e:
            print(e)

    def _setAssetFirmwareVersion(self, type, id, version):
        try:
            v  = int(version)
            db = self._couch[type]

            if id in db:
                d = db[id]
            else:
                d = self._getDBTemplate(type, id)

            d['firmware'] = v
            d['lastseen'] = time.time()
            db.save(d)
        except Exception as e:
            print(e)

    def _process(self):
        k, v = self._workingQueue.get()
        keys = k.split("/")

        if "blanket" == keys[0] or "blouse" == keys[0] or "shoe" == keys[0]:
            if "startup" == keys[2]:
                self._setAssetFirmwareVersion(keys[0], keys[1], v)
            if "ping" == keys[2]:
                self._setAssetLastSeen(keys[0], keys[1])
            if "battery" == keys[2]:
                self._setAssetBatteryLevel(keys[0], keys[1], v)
            if "button" == keys[2]:
                self._mqclient.publish("blouse/000186A0/display/intensity", 0)
                self._mqclient.publish("blouse/000186A0/display/txt/0", "================")
                self._mqclient.publish("blouse/000186A0/display/txt/1", "|| (c) Carla  ||")
                self._mqclient.publish("blouse/000186A0/display/txt/2", "||            ||")
                self._mqclient.publish("blouse/000186A0/display/txt/3", "||    THANK   ||")
                self._mqclient.publish("blouse/000186A0/display/txt/4", "||            ||")
                self._mqclient.publish("blouse/000186A0/display/txt/5", "||     YOU    ||")
                self._mqclient.publish("blouse/000186A0/display/txt/6", "||            ||")
                self._mqclient.publish("blouse/000186A0/display/txt/7", "================")
        else:
            print("key unknown: %s" % k)

    def _configureDB(self):
        for dbname in ['blanket', 'blouse', 'shoe']:
            try:
                db = self._couch[dbname]
            except Exception as e:
                db = self._couch.create(dbname)

    def _getConfig(self):
        self._COUCHDB = os.environ.get("COUCHDB_SERVER", "localhost")
        self._MQTT    = os.environ.get("MQTT_SERVER",    "localhost")

    def __init__(self):
        random.seed
        threading.Thread.__init__(self)
        self.setDaemon(True)
        self._getConfig()
        self._couch                  = couchdb.Server('http://%s:5984/' % self._COUCHDB)
        self._configureDB()
        self._workingQueue           = Queue()
        self._mqclient               = mqtt.Client(clean_session=True)
        self._mqclient.connect(self._MQTT, 1883, 60)
        self._mqclient.on_connect    = self._on_connect
        self._mqclient.on_message    = self._on_message
        self._mqclient.on_disconnect = self._on_disconnect
        self._mqclient.loop_start()
        self._update_heating_time    = time.time()
        self._update_alarm_time      = time.time()
        self._update_blouse_time     = time.time()
        self.start()

    def _on_connect(self, client, userdata, rc, msg):
        print("Connected with result code %s" % rc)
        self._mqclient.subscribe("#")

    def _on_message(self, client, userdata, msg):
        self._workingQueue.put((msg.topic, msg.payload))

    def _on_disconnect(self, client, userdata, msg):
        print("Disconnected")

    def run(self):
        while True:
            try:
                self._process()           # blocks until new mqtt message arrives

            except Exception as e:
                print(e)


if __name__ == '__main__':
    print("11-1-asset started")
    a = Asset()
    time.sleep(42)
