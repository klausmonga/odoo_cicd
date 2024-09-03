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

class remote_params(models.Model):
    _name = 'cicd.remote_params'
    name = fields.Char('name')
    value = fields.Char('value')

class Project(models.Model):
    _name = "cicd.branch"
    name = fields.Text(string="name")
    branch_link = fields.Text(string="Branch Link")
    project_id = fields.Many2one("project.project", string="Github Live Branch")



class Project(models.Model):
    _inherit = "project.project"

    github_link = fields.Text(string="Github link(repository)")
    github_token = fields.Text(string="Github Token")
    github_owner = fields.Text(string="Github Owner")
    github_live_branch = fields.Many2one("cicd.branch",string="Github Live Branch")
    is_repo_created = fields.Boolean(string="Repository created",default=False)
    remote_params_ids = fields.Many2many("cicd.remote_params", string="params")

    broker = '127.0.0.1'
    port = 1883
    topic = "iot/signalisations/framework"
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

        client = mqtt_client.Client(mqtt_client.CallbackAPIVersion.VERSION1, self.client_id)
        # client.username_pw_set(username, password)
        client.on_connect = on_connect
        client.connect(self.broker, self.port)
        return client

    # mosquitto_pub -h 127.0.0.1 -t iot/signalisations -m '{"code_version":2, "code_url": "git@github.com:klausmonga/node.git"}'
    def publish(self, client, report):
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
                json.dump({"log": msg.payload.decode(), }, outfile)
            if json.loads(msg.payload.decode())['flag']:
                client.loop_stop()

        client.subscribe(self.topic_report)
        client.on_message = on_message

    def run_listener(self):
        client = self.connect_mqtt()
        self.subscribe(client)
        client.loop_start()

    def send_report(self, report):
        client = self.connect_mqtt()
        client.loop_start()
        self.publish(client, report)
        client.loop_stop()

    def update_remote_params(self):
        lines = {}
        for param in self.remote_params_ids:
            lines.update({
                param.name: param.value
            })
        self.send_report(lines)
        # self.run_listener()

    def update_repo(self):
        GITHUB_API_URL = "https://api.github.com/"
        headers = {"Authorization": "token {}".format(self.github_token)}
        data = {"name": "{}".format(self.name)}

        r = requests.post(GITHUB_API_URL + "/repos/"+str(self.github_owner)+"/"+str(self.name), data=json.dumps(data), headers=headers)
        if r.status_code == 200:

            branches_url = json.loads(r.text)['branches_url'].replace('{/branch}','')
            r_branch = requests.get(branches_url, data=json.dumps(data), headers=headers)
            if r_branch.status_code == 200:
                all_branches = self.env['cicd.branch'].search([('project_id','=',self.id)])
                if all_branches:
                    for branch in all_branches:
                        branch.unlink()
                for branch in json.loads(r_branch.text):
                    self.env['cicd.branch'].create(
                        {
                            'name': branch['name'],
                            'branch_link': branch['protection_url'].replace('/protection',''),
                            'project_id': self.id,
                        }
                    )
            self.github_link = json.loads(r.text)['ssh_url']
            self.is_repo_created = True
            return {
                'effect': {
                    'fadeout': 'slow',
                    'message': "GITHUB REPOSITORY CREATED",
                    'img_url': '/web/static/img/smile.svg',
                    'type': 'rainbow_man',
                }
            }
        else:
            r = requests.get(GITHUB_API_URL + "repos/" + str(self.github_owner) + "/" + str(self.name)+"/branches",
                              data=json.dumps(data), headers=headers)

            branches_url = json.loads(r.text)['branches_url'].replace('{/branch}', '')
            r_branch = requests.get(branches_url, data=json.dumps(data), headers=headers)
            if r_branch.status_code == 200:
                all_branches = self.env['cicd.branch'].search([('project_id', '=', self.id)])
                if all_branches:
                    for branch in all_branches:
                        branch.unlink()
                for branch in json.loads(r_branch.text):
                    self.env['cicd.branch'].create(
                        {
                            'name': branch['name'],
                            'branch_link': branch['protection_url'].replace('/protection', ''),
                            'project_id': self.id,
                        }
                    )
            self.github_link = json.loads(r.text)['ssh_url']
            self.is_repo_created = True
            return {
                'effect': {
                    'fadeout': 'slow',
                    'message': "GITHUB REPOSITORY CREATED",
                    'img_url': '/web/static/img/smile.svg',
                    'type': 'rainbow_man',
                }
            }

    def create_repo(self):
        GITHUB_API_URL = "https://api.github.com/"
        headers = {"Authorization": "token {}".format(self.github_token)}
        data = {"name": "{}".format(self.name)}

        r = requests.post(GITHUB_API_URL + "user/repos" + "", data=json.dumps(data), headers=headers)
        if r.status_code == 201:
            self.github_link = json.loads(r.text)['ssh_url']
            self.is_repo_created = True
            return {
                'effect': {
                    'fadeout': 'slow',
                    'message': "GITHUB REPOSITORY CREATED",
                    'img_url': '/web/static/img/smile.svg',
                    'type': 'rainbow_man',
                }
            }
        else:
            raise exceptions.UserError(_('repo not created!! '+ r.reason))