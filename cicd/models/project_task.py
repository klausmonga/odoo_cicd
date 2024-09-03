# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import ast
import json
from collections import defaultdict
from datetime import timedelta

from odoo import api, Command, fields, models, _, _lt,exceptions
import requests
import os
import json
import random
from paho.mqtt import client as mqtt_client


class ProjectTask(models.Model):
    _inherit = "project.task"

    code_version = fields.Text(string="Code Version")

    def set_logs(self):
        with open('log.bin', 'r') as outfile:
            tab = outfile.read().replace("}{","}*#{")
            tab = tab.split('*#')
            tasks = []
            for line in tab:
                json_object = json.loads(line)
                tasks.append(self.env['project.task'].create({
                    'name': json.loads(json_object['log'])['test_name']+": "+json.loads(json_object['log'])['message'],
                    'parent_id': self.id,
                    'state':'1_done' if json.loads(json_object['log'])['status'] == 1 else '1_canceled'
                }).id)
            self.write({
                'child_ids':[(6,0,tasks)]
            })

        os.system("rm -fr log.bin")
    @api.onchange('stage_id')
    def onchange_stage_id(self):
        if self:
            if self.stage_id.name == 'TO DEPLOY':
                self.send_report({"code_version": self.code_version, "code_url": self.project_id.github_link})
                self.run_listener()




    broker = '127.0.0.1'
    port = 1883
    topic = "iot/signalisations/app"
    topic_report = "iot/signalisations/report"
    # Generate a Client ID with the subscribe prefix.
    client_id = f'publish-{random.randint(0, 1000)}'
    # username = 'emqx'
    # password = 'public'

    def connect_mqtt(self) -> mqtt_client:
        def on_connect(client, userdata, flags, rc):
            if rc == 0:
                print("Connected to MQTT Broker!")
            else:
                print("Failed to connect, return code %d\n", rc)

        client = mqtt_client.Client(mqtt_client.CallbackAPIVersion.VERSION1,self.client_id)
        # client.username_pw_set(username, password)
        client.on_connect = on_connect
        client.connect(self.broker, self.port)
        return client

    # mosquitto_pub -h 127.0.0.1 -t iot/signalisations -m '{"code_version":2, "code_url": "git@github.com:klausmonga/node.git"}'
    def publish(self,client,report):
            result = client.publish(self.topic, json.dumps(report))
            client.loop_stop()
            # result: [0, 1]
            status = result[0]
            if status == 0:
                print(f"Send `{report}` to topic `{self.topic}`")
            else:
                print(f"Failed to send message to topic {self.topic}")

    def subscribe(self, client: mqtt_client):
        def on_message(client, userdata, msg):
            print(f"Received `{msg.payload.decode()}` from `{msg.topic}` topic")
            # returnstr(msg.payload.decode()))
            with open('log.bin', 'a') as outfile:
                json.dump({"log": msg.payload.decode(),}, outfile)
            if json.loads(msg.payload.decode())['flag']:
                client.loop_stop()


        client.subscribe(self.topic_report)
        client.on_message = on_message


    def run_listener(self):
        client = self.connect_mqtt()
        self.subscribe(client)
        client.loop_start()



    def send_report(self,report):
        client = self.connect_mqtt()
        client.loop_start()
        self.publish(client, report)
        client.loop_stop()
