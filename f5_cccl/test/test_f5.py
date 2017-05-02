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

import pytest

from mock import Mock
from mock import patch

import f5.bigip as bigip
import f5_cccl._f5 as f5

f5.logger = Mock()


def test_log_sequence():
    """Test f5.log_sequence

This is simply covering whether or not the log message is created if the
sequence is or is not present.
    """
    logger = f5.logger
    logger.debug = Mock()
    f5.log_sequence("hello", [])
    assert not logger.debug.called, "No sequence negative test"
    f5.log_sequence("hello", ["world"])
    assert logger.debug.called, "Sequence positive test"


def test_healthcheck_timeout_calculate():
    """Test f5.healthcheck_timeout_calculate

This is simply covering whether or not the math here is performed in the
verified way.  There are other means by which to reach this result; however,
this stands as a good starting point for bug-fix tests down the road.
    """
    data = dict(maxConsecutiveFailures=2, intervalSeconds=2, timeoutSeconds=3)
    expected = 6
    recieved = f5.healthcheck_timeout_calculate(data)
    assert recieved == expected, "Calculation test"


def test_get_protocol():
    """Test f5.get_protocol

This covers the different protocol pairings that are returned with the Fn call.
    """
    expected = dict(tcp='tcp', http='tcp', udp='udp', foo=None)
    for item in expected:
        assert f5.get_protocol(item) == expected[item], \
            "get_protocol({}) test, expected {}".format(item, expected[item])


def test_has_partition():
    """Test f5.has_partition

Checks against the multiple return cases...
    """
    def check_not_app_partition():
        """Checks that not app_partition results in False
        """
        result = f5.has_partition([], False)
        return False if result else True

    def check_star():
        """Checks that a '*' in partitions always results in True
        """
        result = f5.has_partition(['*'], '.')
        return result

    def check_no_partitions_and_not_app_partitions():
        """Redacted for now...  Checks empty partitions and empty app_partition

Raises

This check has been removed for now as it appears to be a bug in the code due
to the fact that this conditional statement will never be reached.

This check only verifies that the conditional causes a raised Exception.
        """
        with pytest.raises(Exception):
            f5.has_partition([], '.')
        return True  # should raise passed this otherwise...

    def check_app_partition_present():
        """Check that app_partition in partitions results in True
        """
        fun = 'hello world'
        result = f5.has_partition([fun], fun)
        return result

    def check_default():
        """Checks that the default case is False
        """
        fun = 'hello world'
        result = f5.has_partition(['no'], fun)
        return False if result else True

    check_list = [check_not_app_partition, check_star,
                  # check_no_partitions_and_not_app_partitions,
                  check_app_partition_present, check_default]
    for check in check_list:
        assert check(), "{0!r}".format(check)


class TestCloudBigIP(object):
    @pytest.fixture(autouse=True)
    def init(self, request):
        request.addfinalizer(self.teardown)
        self.get_protocol = f5.get_protocol

    def teardown(self):
        f5.get_protocol = self.get_protocol

    @pytest.fixture()
    def bigip_mock(self, request):
        bigip.BigIP = Mock()

    @pytest.fixture()
    def clean_mocks(self):
        f5.logger.reset_mock

    @pytest.fixture()
    def construct_app(self):
        app = Mock()
        app.servicePort = 256
        app.bindAddr = 'foo'
        app.balance = 'round-robin'
        self.app = app

    @pytest.fixture()
    def get_bigip(self, bigip_mock):
        self.host = 'ht'
        self.port = 'pt'
        self.username = 'un'
        self.partitions = ['foo', 'doo']
        with patch('f5.bigip.BigIP.__init__', Mock(), create=True):
            bigip = f5.BigIP(self.host, self.port, self.username,
                             self.partitions)
        self.bigip = bigip

    @pytest.fixture()
    def mock_get_protocol(self, request):
        f5.get_protocol = Mock(return_value=True)

    def test__init__(self, bigip_mock):
        host = 'ht'
        port = 'pt'
        username = 'un'
        partitions = []
        token = None
        parent_foo = Mock()
        with patch('f5.bigip.BigIP.__init__', parent_foo, create=True):
            check = f5.CloudBigIP(host, port, username, partitions, token)
        assert parent_foo.called, "Parent was called properly"
        assert check._hostname == host, "Host Check"
        assert check._port == port, "port check"
        assert check._username == username, "username check"
        assert check._partitions == partitions, "partitions check"
        assert check._lbmethods, "assignment of lbmethods"

    def test_get_partitions(self, get_bigip):
        bigip = self.bigip
        assert self.partitions == bigip.get_partitions(), "BigIP._partitions()"

    def test_is_label_data_valid__invalid_mode(self, clean_mocks, construct_app,
                                               get_bigip, mock_get_protocol):
        f5.get_protocol.return_value = None
        result = self.bigip.is_label_data_valid(self.app)
        assert not result, "Check Negative Validate mode"
        assert f5.logger.error.called, "Logged an error about it..."

    def test_is_label_data_valid__invalid_port(self, clean_mocks, construct_app,
                                               get_bigip, mock_get_protocol):
        self.app.service_port = 0
        result = self.bigip.is_label_data_valid(self.app)
        assert not result, "Invalid serviceport test"
        assert f5.logger.error.called, "Logged an error about it..."

    def test_is_label_data_valid__invalid_address(self, clean_mocks,
                                                  construct_app, get_bigip,
                                                  mock_get_protocol):
        self.app.binAddr = None
        result = self.bigip.is_label_data_valid(self.app)
        assert not result, "Invalid binAddr test"
        assert f5.logger.error.called, "Logged an error about it..."

    def test_is_label_data_valid__invalid_lb_method(self, clean_mocks,
                                                    construct_app, get_bigip,
                                                    mock_get_protocol):
        self.app.balance = 'broke'
        result = self.bigip.is_label_data_valid(self.app)
        assert not result, "Invalid LB method test"
        assert f5.logger.error.called, "Logged an error about it..."

    def test_is_label_data_valid(self, clean_mocks, construct_app, get_bigip,
                                 mock_get_protocol):
        result = self.bigip.is_label_data_valid(self.app)
        assert result, "Validation test did not work!"
        assert not f5.logger.error.called, "Successfully not logged anything..."
