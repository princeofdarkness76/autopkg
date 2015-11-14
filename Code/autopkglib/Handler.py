#!/usr/bin/env python
#
# Copyright 2010 Per Olofsson
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import sys
import re
import plistlib


__all__ = [
    "Handler",
    "HandlerError"
]


re_keyref = re.compile(r'%(?P<key>[a-zA-Z_][a-zA-Z_0-9]*)%')


class HandlerError(BaseException):
    pass

class Handler(object):
    """Base class for handlers and processors."""
    
    def __init__(self, env=None, infile=None, outfile=None):
        super(Handler, self).__init__()
        self.env = env
        if infile is None:
            self.infile = sys.stdin
        else:
            self.infile = infile
        if outfile is None:
            self.outfile = sys.stdout
        else:
            self.outfile = outfile
    
    def read_input_plist(self):
        """Read environment from input plist."""
        
        try:
            indata = self.infile.read()
            if indata:
                self.env = plistlib.readPlistFromString(indata)
            else:
                self.env = dict()
        except BaseException as e:
            raise HandlerError(e)
    
    def write_output_plist(self):
        """Write environment to output as plist."""
        
        if self.env is None:
            return
        
        try:
            plistlib.writePlist(self.env, self.outfile)
        except BaseException as e:
            raise HandlerError(e)
    
    def update_data(self, key, value):
        """Update environment keys with value. Existing keys can be referenced
        by wrapping the key in %percent% signs."""
        
        def getdata(m):
            return self.env[m.group("key")]
            
        def do_variable_substitution(item):
            """Do variable substitution for item"""
            if isinstance(item, str):
                item = re_keyref.sub(getdata, item)
            elif isinstance(item, list):
                for index in range(len(item)):
                    item[index] = do_variable_substitution(item[index])
            elif isinstance(item, dict):
                for key, value in item.iteritems():
                    item[key] = do_variable_substitution(value)
            return item
        
        self.env[key] = do_variable_substitution(value)
    
    def inject(self, arguments):
        # Update data with arguments.
        for key, value in arguments.items():
            self.update_data(key, value)
