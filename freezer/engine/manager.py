"""
(c) Copyright 2016 Hewlett-Packard Development Enterprise, L.P.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

"""

import os
from oslo_config import cfg
from oslo_log import log
from oslo_utils import importutils

from freezer.exceptions import engine as engine_exceptions

CONF = cfg.CONF
LOG = log.getLogger(__name__)


class EngineManager(object):
    """
    EngineManager, this class handles engines.
        Lists all available engines
        Load an engine
        Checks if an engine does exists or not
    """
    def __init__(self):
        """
        This function does some initialization for the engine manager and
        register some variables from the CONF variable into the local class
        """
        self.engine_name = CONF.engine_name
        self.engine_store = os.path.abspath(os.path.dirname(__file__))
        self.engines = []

    def load_engine(self, **kwargs):
        """ Check if the engine exists or not. If not raise EngineNotFound
        Error. If the engine exists then try to get an instance of this engine.
        """
        if not self._check_engine_exists():
            raise engine_exceptions.EngineNotFound(
                "Engine {0} not found".format(self.engine_name)
            )
        return importutils.import_object(
            "freezer.engine.{0}.{0}.{1}Engine".format(
                self.engine_name,
                self.engine_name.capitalize()
            ),
            **kwargs
        )

    def _check_engine_exists(self):
        engines = self.list_engines()
        if self.engine_name not in engines:
            return False
        return True

    def list_engines(self):
        """
        Lists all engines in the engine directory
        :return:
        """
        engines = [
            name for name in os.listdir(self.engine_store) if
            os.path.isdir(os.path.join(self.engine_store, name))
        ]
        self.engines = engines
        return engines
