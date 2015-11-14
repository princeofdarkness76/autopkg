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
import subprocess
from ..Handler import Handler, HandlerError


__all__ = [
    "Processor",
    "ProcessorError"
]


class ProcessorError(HandlerError):
    pass

class Processor(Handler):
    """Processor base class.
    
    Processors accept a property list as input, process its contents, and
    returns a new or updated property list that can be processed further.
    """
    
    def __init__(self, env=None, infile=None, outfile=None):
        super(Processor, self).__init__(env, infile, outfile)
    
    def main(self):
        raise ProcessorError("Abstract method main() not implemented.")
    
    def get_manifest(self):
        try:
            return (self.description,
                    self.input_variables,
                    self.output_variables)
        except AttributeError as e:
            raise ProcessorError("Missing manifest: %s" % e)
    
    def process(self):
        """Main processing loop."""
        
        # Make sure all required arguments have been supplied.
        for variable, flags in self.input_variables.items():
            if flags["required"] and (variable not in self.env):
                raise ProcessorError(
                    "%s requires %s" % (self.__name__, variable))
        
        self.main()
        return self.env
    
    def parse_arguments(self):
        """Parse commandline arguments as key='value'."""
        
        for arg in sys.argv[1:]:
            (key, sep, value) = arg.partition("=")
            if sep != "=":
                raise ProcessorError("Illegal argument '%s'" % arg)
            self.update_data(key, value)
    
    def execute_shell(self):
        """Execute as a standalone binary on the commandline."""
        
        try:
            self.read_input_plist()
            self.parse_arguments()
            self.main()
            self.write_output_plist()
        except ProcessorError as e:
            print >> sys.stderr, "ProcessorError: %s" % e
            sys.exit(10)
        else:
            sys.exit(0)
        

