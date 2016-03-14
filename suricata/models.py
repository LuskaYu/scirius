"""
Copyright(C) 2014, Stamus Networks
Written by Eric Leblond <eleblond@stamus-networks.com>

This file is part of Scirius.

Scirius is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Scirius is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Scirius.  If not, see <http://www.gnu.org/licenses/>.
"""

from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone

# Create your models here.
import os

from rules.models import Ruleset


def validate_hostname(value):
    if ' ' in value:
        raise ValidationError('"%s" contains space' % value)

class Suricata(models.Model):
    name = models.CharField(max_length=100, unique = True, validators = [validate_hostname])
    descr = models.CharField(max_length=400)
    output_directory = models.CharField(max_length=400)
    created_date = models.DateTimeField('date created')
    updated_date = models.DateTimeField('date updated', blank = True)
    ruleset = models.ForeignKey(Ruleset, blank = True, null = True, on_delete=models.SET_NULL)

    editable = True

    def __unicode__(self):
        return self.name

    def generate(self):
        # FIXME extract archive file for sources
        # generate rule file
        rules = self.ruleset.generate()
        # write to file
        rfile = open(self.output_directory + "/" + "scirius.rules", 'w')
        header = "# Rules file for " + self.name + " using ruleset " + self.ruleset.name + " generated by Scirius at " + str(timezone.now()) + "\n"
        rfile.write(header.encode('utf-8'))
        for rule in rules:
            try:
                rfile.write(rule.content)
            except:
                rfile.write(rule.content.encode('utf-8'))
        rfile.close()
        # export files at version
        self.ruleset.export_files(self.output_directory)

    def push(self):
        # For now we just create a file asking for reload
        # It will cause an external script to reload suricata rules
        reload_file = os.path.join(self.output_directory, "scirius.reload")
        self.updated_date = timezone.now()
        self.save()
        if os.path.isfile(reload_file):
            return False
        rfile = open(reload_file, 'w')
        rfile.write(str(timezone.now()))
        rfile.close()
        # In case user has changed configuration file before reloading
        self.ruleset.needs_test()
        return True

def get_probe_hostnames(limit = 10):
    suricata = Suricata.objects.all()
    if suricata != None:
        return [ suricata[0].name ]
    return None
