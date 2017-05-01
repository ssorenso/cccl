#!/usr/bin/env python
# Copyright 2017 F5 Networks Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

# import pytest

from mock import Mock

import f5_cccl._f5 as f5

f5.logger = Mock()


def test_log_sequence():
    logger = f5.logger
    logger.debug = Mock()
    f5.log_sequence("hello", [])
    assert not logger.debug.called, "No sequence negative test"
    f5.log_sequence("hello", ["world"])
    assert logger.debug.called, "Sequence positive test"


def test_healthcheck_timeout_calculate():
    data = dict(maxConsecutiveFailures=2, intervalSeconds=2, timeoutSeconds=3)
    expected = 6
    recieved = f5.healthcheck_timeout_calculate(data)
    assert recieved == expected, "Calculation test"
