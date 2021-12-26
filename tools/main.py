# -*- coding: utf-8 -*-
import argparse
import json
import os
import sys
import time

from tencentcloud.common import credential
from tencentcloud.common.profile.client_profile import ClientProfile
from tencentcloud.common.profile.http_profile import HttpProfile
from tencentcloud.cam.v20190116 import cam_client, models


class Client:

    def __init__(self, secret_id, secret_key, endpoint):
        cred = credential.Credential(secret_id, secret_key)
        http_profile = HttpProfile()
        http_profile.endpoint = endpoint

        client_profile = ClientProfile()
        client_profile.httpProfile = http_profile
        self.client = cam_client.CamClient(cred, "", client_profile)

    def list_policies(self):
        client = self.client
        req = models.ListPoliciesRequest()
        policies = []
        page = 1

        for _ in range(1000):
            params = {
                "Rp": 200,
                "Page": page,
                "Scope": "QCS",
            }
            req.from_json_string(json.dumps(params))
            resp = client.ListPolicies(req)
            if not resp.List:
                break

            for info in resp.List:
                info.Description = None
                info.Attachments = None
                info.AttachEntityCount = None
                info.AttachEntityBoundaryCount = None
                policies.append(info)

            page += 1

        return sorted(policies, key=lambda x: x.PolicyId)

    def get_policy(self, policy_id):
        client = self.client
        req = models.GetPolicyRequest()
        params = {
            "PolicyId": policy_id,
        }
        req.from_json_string(json.dumps(params))

        resp = client.GetPolicy(req)
        resp.RequestId = None
        resp.Description = None
        return resp


def model_to_json(m):
    return json.dumps(m._serialize(allow_none=False), indent=' ',
                      sort_keys=True, ensure_ascii=True)


def model_to_dict(m):
    s = model_to_json(m)
    return json.loads(s)


def model_list_to_json(m):
    return json.dumps([model_to_dict(x) for x in m], indent=' ',
                      sort_keys=True, ensure_ascii=True)


def pretty_json_str(s):
    if not s:
        return s

    obj = json.loads(s)
    return json.dumps(obj, indent=' ', sort_keys=True, ensure_ascii=True)


def ensure_mdir(dir):
    try:
        os.mkdir(dir)
    except FileExistsError:
        pass


def save_policy(client, policy_id, dir):
    policy = client.get_policy(policy_id)
    name = policy.PolicyName

    dir = os.path.join(dir, name)
    ensure_mdir(dir)

    with open(os.path.join(dir, 'policy.json'), 'w') as fp:
        fp.write(model_to_json(policy))
    with open(os.path.join(dir, 'policy_document.json'), 'w') as fp:
        fp.write(pretty_json_str(policy.PolicyDocument))

    print('saved {}'.format(name))


def main():
    arg = argparse.ArgumentParser()
    arg.add_argument('--endpoint', default='cam.tencentcloudapi.com')
    arg.add_argument('--policies-dir', default='policies')
    arg.add_argument('--policies-list-file', default='policies-list.json')
    options = arg.parse_args()

    client = Client(os.environ['TENCENT_SECRET_ID'], os.environ['TENCENT_SECRET_KEY'],
                    options.endpoint)
    policies = client.list_policies()
    with open(options.policies_list_file, 'w') as fp:
        fp.write(model_list_to_json(policies))
    print('saved {}'.format(options.policies_list_file))

    n = 0
    for p in policies:
        n += 1
        if n % 20 == 0:
            time.sleep(1)
        save_policy(client, p.PolicyId, options.policies_dir)


if __name__ == '__main__':
    main()
