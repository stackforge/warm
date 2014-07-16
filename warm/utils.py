#   Copyright 2013 Cloudwatt
#
#   Author: Sahid Orentino Ferdjaoui <sahid.ferdjaoui@cloudwatt.com>
#
#   Licensed under the Apache License, Version 2.0 (the "License"); you may
#   not use this file except in compliance with the License. You may obtain
#   a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#   WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#   License for the specific language governing permissions and limitations
#   under the License.

"""Some utilities script to be used with warm."""

from email.mime import multipart
from email.mime import text
import os


MULTIPART_MAPPINGS = {
    '#include': 'text/x-include-url',
    '#!': 'text/x-shellscript',
    '#cloud-config': 'text/cloud-config',
    '#upstart-job': 'text/upstart-job',
    '#part-handler': 'text/part-handler',
    '#cloud-boothook': 'text/cloud-boothook'
}


def get_type(fname, deftype="text/plain"):
    rtype = deftype
    with open(fname, "rb") as f:
        line = f.readline()
        for s, mtype in MULTIPART_MAPPINGS.items():
            if line.startswith(s):
                rtype = mtype
                break
    return rtype


def multipart_content(*files):
    """Returns a mutlipart content.

    Note: This script was clearly inspired by write-mime-multipart.
    """
    outer = multipart.MIMEMultipart()
    for fname in files:
        mtype = get_type(fname)
        maintype, subtype = mtype.split('/', 1)
        with open(fname) as f:
            msg = text.MIMEText(f.read(), _subtype=subtype)
        msg.add_header('Content-Disposition', 'attachment',
                       filename=os.path.basename(fname))
        outer.attach(msg)
    return outer.as_string()
