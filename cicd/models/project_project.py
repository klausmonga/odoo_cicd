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
            raise exceptions.UserError(_('repo not created!! ' + r.reason))

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