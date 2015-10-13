#!/usr/bin/env python
# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2015, Numenta, Inc.  Unless you have purchased from
# Numenta, Inc. a separate commercial license for this software code, the
# following terms and conditions apply:
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero Public License version 3 as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU Affero Public License for more details.
#
# You should have received a copy of the GNU Affero Public License
# along with this program.  If not, see http://www.gnu.org/licenses.
#
# http://numenta.org/licenses/
# ----------------------------------------------------------------------

"""
unit tests for taurus.metric_collectors.metric_utils
"""

# Disable warning "access to protected member" and "method could be a function"
# pylint: disable=W0212,R0201


from datetime import datetime, timedelta
import json
import logging
import time
import unittest

import mock
from mock import ANY, MagicMock, Mock, patch


import sqlalchemy

from nta.utils.test_utils import time_test_utils

from taurus.metric_collectors import metric_utils



class MetricUtilsTestCase(unittest.TestCase):


  def testAggTimestampFromSampleTimestamp(self):
    # Ref precedes sample timestamp
    sampleTs = datetime(2015, 02, 20, 02, 10, 00)
    refTs =    datetime(2014, 02, 20, 02, 00, 00)
    self.assertEqual(
      metric_utils.aggTimestampFromSampleTimestamp(
        sampleDatetime=sampleTs,
        aggRefDatetime=refTs,
        aggSec=300),
      datetime(2015, 02, 20, 2, 10, 00))

    sampleTs = datetime(2015, 02, 20, 02, 11, 00)
    refTs =    datetime(2014, 02, 20, 02, 00, 00)
    self.assertEqual(
      metric_utils.aggTimestampFromSampleTimestamp(
        sampleDatetime=sampleTs,
        aggRefDatetime=refTs,
        aggSec=300),
      datetime(2015, 02, 20, 2, 10, 00))

    sampleTs = datetime(2015, 02, 20, 02, 14, 00)
    refTs =    datetime(2014, 02, 20, 02, 00, 00)
    self.assertEqual(
      metric_utils.aggTimestampFromSampleTimestamp(
        sampleDatetime=sampleTs,
        aggRefDatetime=refTs,
        aggSec=300),
      datetime(2015, 02, 20, 2, 10, 00))

    sampleTs = datetime(2015, 02, 20, 02, 15, 00)
    refTs =    datetime(2014, 02, 20, 02, 00, 00)
    self.assertEqual(
      metric_utils.aggTimestampFromSampleTimestamp(
        sampleDatetime=sampleTs,
        aggRefDatetime=refTs,
        aggSec=300),
      datetime(2015, 02, 20, 2, 15, 00))

    # Ref follows sample timestamp
    sampleTs = datetime(2015, 02, 20, 02, 10, 00)
    refTs =    datetime(2016, 01, 17, 05, 20, 00)
    self.assertEqual(
      metric_utils.aggTimestampFromSampleTimestamp(
        sampleDatetime=sampleTs,
        aggRefDatetime=refTs,
        aggSec=300),
      datetime(2015, 02, 20, 2, 10, 00))

    sampleTs = datetime(2015, 02, 20, 02, 14, 00)
    refTs =    datetime(2016, 01, 17, 05, 20, 00)
    self.assertEqual(
      metric_utils.aggTimestampFromSampleTimestamp(
        sampleDatetime=sampleTs,
        aggRefDatetime=refTs,
        aggSec=300),
      datetime(2015, 02, 20, 2, 10, 00))

    sampleTs = datetime(2015, 02, 20, 02, 15, 00)
    refTs =    datetime(2016, 01, 17, 05, 20, 00)
    self.assertEqual(
      metric_utils.aggTimestampFromSampleTimestamp(
        sampleDatetime=sampleTs,
        aggRefDatetime=refTs,
        aggSec=300),
      datetime(2015, 02, 20, 2, 15, 00))

    sampleTs = datetime(2015, 02, 20, 02, 15, 00)
    refTs =    datetime(2016, 01, 17, 05, 21, 00)
    self.assertEqual(
      metric_utils.aggTimestampFromSampleTimestamp(
        sampleDatetime=sampleTs,
        aggRefDatetime=refTs,
        aggSec=300),
      datetime(2015, 02, 20, 2, 11, 00))

    # Ref equals sample timestamp
    sampleTs = datetime(2015, 02, 20, 02, 14, 00)
    refTs =    datetime(2015, 02, 20, 02, 14, 00)
    self.assertEqual(
      metric_utils.aggTimestampFromSampleTimestamp(
        sampleDatetime=sampleTs,
        aggRefDatetime=refTs,
        aggSec=300),
      datetime(2015, 02, 20, 02, 14, 00))


  def testGetMetricsConfiguration(self):
    metrics = metric_utils.getMetricsConfiguration()
    self.assertIsInstance(metrics, dict)
    self.assertTrue(metrics)
    for companyName, details in metrics.iteritems():
      self.assertIsInstance(companyName, basestring)
      self.assertIsInstance(details, dict)
      self.assertTrue(details)
      self.assertIn("metrics", details)
      self.assertIn("stockExchange", details)
      self.assertIn("symbol", details)
      for metricName, metric in details["metrics"].iteritems():
        self.assertIsInstance(metricName, basestring)
        self.assertIsInstance(metric, dict)
        self.assertTrue(metric)
        self.assertIn("metricType", metric)
        self.assertIn("metricTypeName", metric)
        self.assertIn("modelParams", metric)
        self.assertIn("provider", metric)
        if metric["provider"] == "twitter":
          self.assertIn("screenNames", metric)
        elif metric["provider"] == "xignite":
          self.assertIn("sampleKey", metric)


  def testGetMetricNamesFromConfig(self):
    jsonConfig = (
      """
      {
        "3M": {
          "metrics": {
            "TWITTER.TWEET.HANDLE.MMM.VOLUME": {
              "metricType": "TwitterVolume",
              "metricTypeName": "Twitter Volume",
              "modelParams": {
                "minResolution": 0.6
              },
              "provider": "twitter",
              "screenNames": [
                "3M"
              ]
            },
            "XIGNITE.MMM.VOLUME": {
              "metricType": "StockVolume",
              "metricTypeName": "Stock Volume",
              "modelParams": {
                "minResolution": 0.2
              },
              "provider": "xignite",
              "sampleKey": "Volume"
            }
          },
          "stockExchange": "NYSE",
          "symbol": "MMM"
        },
        "ACE Ltd": {
          "metrics": {
            "TWITTER.TWEET.HANDLE.ACE.VOLUME": {
              "metricType": "TwitterVolume",
              "metricTypeName": "Twitter Volume",
              "modelParams": {
                "minResolution": 0.6
              },
              "provider": "twitter",
              "screenNames": []
            },
            "XIGNITE.ACE.CLOSINGPRICE": {
              "metricType": "StockPrice",
              "metricTypeName": "Stock Price",
              "modelParams": {
                "minResolution": 0.2
              },
              "provider": "xignite",
              "sampleKey": "Close"
            }
          },
          "stockExchange": "NYSE",
          "symbol": "ACE"
        }
      }
      """
    )
    metricNames = metric_utils.getMetricNamesFromConfig(json.loads(jsonConfig))

    expected = [
      "TWITTER.TWEET.HANDLE.MMM.VOLUME",
      "XIGNITE.MMM.VOLUME",
      "TWITTER.TWEET.HANDLE.ACE.VOLUME",
      "XIGNITE.ACE.CLOSINGPRICE"
    ]
    self.assertItemsEqual(expected, metricNames)


  def testGetAllMetricSecurities(self):
    securities = metric_utils.getAllMetricSecurities()
    self.assertIsInstance(securities, tuple)
    self.assertTrue(securities)
    for security in securities:
      self.assertEqual(len(security), 2)
      symbol, exchange = security
      self.assertIsInstance(symbol, basestring)
      self.assertIsInstance(exchange, basestring)
      self.assertIn(exchange, ("NASDAQ", "NYSE"))


  def testGetMetricSymbolsForProvider(self):
    securities = metric_utils.getMetricSymbolsForProvider("xignite")
    self.assertIsInstance(securities, tuple)
    self.assertTrue(securities)
    for security in securities:
      self.assertEqual(len(security), 2)
      symbol, exchange = security
      self.assertIsInstance(symbol, basestring)
      self.assertIsInstance(exchange, basestring)
      self.assertIn(exchange, ("NASDAQ", "NYSE"))


  @patch("taurus.metric_collectors.metric_utils.requests", autospec=True)
  def testCreateAllModelsHappyPath(self, requestsMock):
    requestsMock.post.return_value = Mock(status_code=201,
                                          text='[{"uid":"foo", "name":"bar"}]')

    totalModels = len(
      metric_utils.getMetricNamesFromConfig(
        metric_utils.getMetricsConfiguration()))

    metric_utils.createAllModels("localhost", "taurus")
    self.assertEqual(requestsMock.post.call_count, totalModels)

    for args, kwargs in requestsMock.post.call_args_list:
      self.assertEqual(args[0], "https://localhost/_models")
      self.assertIn("data", kwargs)
      data = json.loads(kwargs["data"])
      self.assertIsInstance(data, dict)
      self.assertIn("datasource", data)
      self.assertEquals(data["datasource"], "custom")
      self.assertIn("metricSpec", data)
      self.assertIn("metric", data["metricSpec"])
      self.assertIn("resource", data["metricSpec"])
      self.assertIn("userInfo", data["metricSpec"])
      self.assertIsInstance(data["metricSpec"]["userInfo"], dict)
      self.assertIn("metricType", data["metricSpec"]["userInfo"])
      self.assertIn("metricTypeName", data["metricSpec"]["userInfo"])
      self.assertIn("symbol", data["metricSpec"]["userInfo"])
      self.assertIn("modelParams", data)


  @patch("taurus.metric_collectors.metric_utils.createCustomHtmModel",
         autospec=True)
  def testCreateAllModelsWithMetricNameFilter(self, createCustomHtmModelMock):
    allMetricNames = metric_utils.getMetricNamesFromConfig(
      metric_utils.getMetricsConfiguration())

    subsetOfMetricNames = allMetricNames[:(len(allMetricNames) + 1) // 2]
    self.assertGreater(len(subsetOfMetricNames), 0)

    createCustomHtmModelMock.side_effect = (
      lambda **kwargs: dict(name=kwargs["metricName"],
                            uid=kwargs["metricName"] * 2))

    models = metric_utils.createAllModels(host="host",
                                          apiKey="apikey",
                                          onlyMetricNames=subsetOfMetricNames)

    self.assertEqual(createCustomHtmModelMock.call_count,
                     len(subsetOfMetricNames))

    self.assertEqual(len(models), len(subsetOfMetricNames))

    self.assertItemsEqual(subsetOfMetricNames,
                          [model["name"] for model in models])


  def testCreateAllModelsWithEmptyMetricFilter(self):
    with self.assertRaises(ValueError) as assertContext:
      metric_utils.createAllModels(host="host",
                                   apiKey="apikey",
                                   onlyMetricNames=[])

    self.assertEqual(assertContext.exception.args[0],
                     "onlyMetricNames is empty")


  def testCreateAllModelsWithDuplicatesInMetricFilter(self):
    with self.assertRaises(ValueError) as assertContext:
      metric_utils.createAllModels(host="host",
                                   apiKey="apikey",
                                   onlyMetricNames=["a", "a", "b"])

    self.assertEqual(assertContext.exception.args[0],
                     "onlyMetricNames contains duplicates")


  def testCreateAllModelsWithUnknownsInMetricFilter(self):
    with self.assertRaises(ValueError) as assertContext:
      metric_utils.createAllModels(host="host",
                                   apiKey="apikey",
                                   onlyMetricNames=["a", "b"])

    self.assertIn(
      "elements in onlyMetricNames are not in metrics configuration",
      assertContext.exception.args[0])


  @patch("taurus.metric_collectors.metric_utils.time.sleep", autospec=True)
  @patch("taurus.metric_collectors.metric_utils.requests", autospec=True)
  def testCreateAllModelsWithErrors(self, requestsMock, _sleepMock):
    requestsMock.post.return_value = Mock(status_code=500,
                                          text="Server limit exceeded")

    self.assertRaises(metric_utils.ModelQuotaExceededError,
                      metric_utils.createAllModels, "localhost", "taurus")

    requestsMock.post.return_value = Mock()

    self.assertRaises(metric_utils.RetriesExceededError,
                      metric_utils.createAllModels, "localhost", "taurus")


  def testFilterCompanyMetricNamesBySymbol(self):
    negatives = [
      "TWITTER.TWEET.HANDLE.ZZZ.VOLUME",
      "XIGNITE.ZZZ.CLOSINGPRICE",
      "XIGNITE.FOOBARZZZ.CLOSINGPRICE",
      "XIGNITE.ZZZFOOBAR.CLOSINGPRICE",
      "XIGNITE.FOOBAR.ZZZ.VOLUME",
      "XIGNITE.NEWS.FOOBAR.ZZZ.VOLUME",
      "FOOBAR.VOLUME",
      ".FOOBAR.CLOSINGPRICE",
      "XIGNITE.FOOBAR.",
      "FOOBARCLOSINGPRICE",
    ]

    positives = [
      "XIGNITE.FOOBAR.CLOSINGPRICE",
      "XIGNITE.FOOBAR.VOLUME",
      "TWITTER.TWEET.HANDLE.FOOBAR.VOLUME",
      "XIGNTE.NEWS.FOOBAR.VOLUME",
    ]

    # Execute
    filteredNames = metric_utils.filterCompanyMetricNamesBySymbol(
      metricNames=negatives + positives,
      tickerSymbol="FOOBAR")

    # Verify that the expected metric names were returned

    self.assertItemsEqual(positives, filteredNames)


  @patch("taurus.metric_collectors.metric_utils.requests", autospec=True)
  def testDeleteMetric(self, requestsMock):
    requestsMock.delete.return_value = Mock(status_code=200)

    metric_utils.deleteMetric(host="localhost",
                              apiKey="taurus",
                              metricName="XIGNITE.FOO.VOLUME")
    requestsMock.delete.assert_called_once_with(
      "https://localhost/_metrics/custom/XIGNITE.FOO.VOLUME",
      auth=("taurus", ""), verify=ANY)


  @patch("taurus.metric_collectors.metric_utils.requests", autospec=True)
  def testDeleteMetricMetricNotFound(self, requestsMock):
    requestsMock.delete.return_value = Mock(status_code=404,
                                            text="metric not found")

    with self.assertRaises(metric_utils.MetricNotFound) as errorContext:
      metric_utils.deleteMetric(host="localhost",
                                apiKey="taurus",
                                metricName="XIGNITE.FOO.VOLUME")

    requestsMock.delete.assert_called_once_with(
      "https://localhost/_metrics/custom/XIGNITE.FOO.VOLUME",
      auth=("taurus", ""), verify=ANY)

    self.assertEqual(errorContext.exception.args[0], "metric not found")


  @patch("taurus.metric_collectors.metric_utils.requests", autospec=True)
  def testGetAllModels(self, requestsMock):

    # We'll mock out only the minimal response that would be required to
    # satisfy the requirements of metric_utils.getAllModels(), and then
    # assert that the returned result is the json-decoded response from the
    # mocked out API.
    requestsMock.get.return_value = Mock(status_code=200,
                                         text='[{"parameters":"True"}]')

    result = metric_utils.getAllModels("localhost", "taurus")

    requestsMock.get.assert_called_once_with("https://localhost/_models",
                                             verify=ANY, auth=("taurus", ""))

    self.assertSequenceEqual(result, ({"parameters":"True"},))


  @patch("taurus.metric_collectors.metric_utils.time.sleep", autospec=True)
  @patch("taurus.metric_collectors.metric_utils.requests", autospec=True)
  def testGetAllModelsWithErrors(self, requestsMock, _sleepMock):

    requestsMock.get.return_value = Mock()

    self.assertRaises(metric_utils.RetriesExceededError,
                      metric_utils.getAllModels, "localhost", "taurus")

    requestsMock.get.assert_called_with("https://localhost/_models",
                                        verify=ANY, auth=("taurus", ""))


  @patch("taurus.metric_collectors.metric_utils.requests", autospec=True)
  def testGetOneModel(self, requestsMock):

    # We'll mock out only the minimal response that would be required to
    # satisfy the requirements of metric_utils.getAllModels(), and then
    # assert that the returned result is the json-decoded response from the
    # mocked out API.
    requestsMock.get.return_value = Mock(status_code=200,
                                         text='[{"parameters":"True"}]')

    result = metric_utils.getOneModel("localhost", "taurus", "foo")

    requestsMock.get.assert_called_once_with("https://localhost/_models/foo",
                                             verify=ANY, auth=("taurus", ""))

    self.assertEqual(result, {"parameters":"True"})


  @patch("taurus.metric_collectors.metric_utils.time.sleep", autospec=True)
  @patch("taurus.metric_collectors.metric_utils.requests", autospec=True)
  def testGetOneModelWithErrors(self, requestsMock, _sleepMock):

    requestsMock.get.return_value = Mock()

    self.assertRaises(metric_utils.RetriesExceededError,
                      metric_utils.getOneModel, "localhost", "taurus", "foo")

    requestsMock.get.assert_called_with("https://localhost/_models/foo",
                                        verify=ANY, auth=("taurus", ""))


  @patch("taurus.metric_collectors.metric_utils.requests", autospec=True)
  def testGetAllModelIds(self, requestsMock):

    # We'll mock out only the minimal response that would be required to
    # satisfy the requirements of metric_utils.getAllModels(), and then
    # assert that the returned result is the json-decoded response from the
    # mocked out API.
    requestsMock.get.return_value = Mock(
      status_code=200,
      text='[{"uid":"foo", "parameters":"True"}]'
    )

    result = metric_utils.getAllModelIds("localhost", "taurus")

    requestsMock.get.assert_called_once_with("https://localhost/_models",
                                             verify=ANY, auth=("taurus", ""))

    self.assertSequenceEqual(result, ("foo",))


  @patch("taurus.metric_collectors.metric_utils.datetime",
         autospec=True)
  @patch("taurus.metric_collectors.metric_utils.collectorsdb", autospec=True)
  def testEstablishLastEmittedSampleDatetime(self, collectorsdbMock,
                                             datetimeMock):

    fakeNow = datetime(1997, 8, 29, 2, 14)
    datetimeMock.utcnow.return_value = fakeNow

    # Test with non-None queryLastEmittedSampleDatetime() result

    collectorsdbMock.engineFactory.return_value = Mock(
      spec_set=sqlalchemy.engine.Engine)
    result = metric_utils.establishLastEmittedSampleDatetime(
      "twitter-tweets-volume", 300)

    self.assertEqual(result, (collectorsdbMock
                              .engineFactory
                              .return_value
                              .execute
                              .return_value
                              .scalar
                              .return_value))

    # Test again with None queryLastEmittedSampleDatetime() result

    collectorsdbMock.engineFactory.return_value.execute.reset_mock()
    with patch("taurus.metric_collectors.metric_utils"
               ".queryLastEmittedSampleDatetime") \
         as queryLastEmittedSampleDatetime:
      queryLastEmittedSampleDatetime.return_value = None
      result = metric_utils.establishLastEmittedSampleDatetime(
        "twitter-tweets-volume", 300)

      args, _ = (
        collectorsdbMock.engineFactory.return_value.execute.call_args_list[0])

      params = args[0].compile().construct_params()

      self.assertEqual(params["sample_ts"].microsecond, 0)
      self.assertEqual(fakeNow - params["sample_ts"], timedelta(seconds=300))
      self.assertEqual(queryLastEmittedSampleDatetime.call_count, 2)
      args, _ = (collectorsdbMock
                 .engineFactory
                 .return_value
                 .execute
                 .call_args_list[0])
      self.assertTrue(args)
      self.assertIsInstance(args[0], sqlalchemy.sql.dml.Insert)


  @patch("taurus.metric_collectors.metric_utils.collectorsdb", autospec=True)
  def testUpdateLastEmittedNonMetricSequence(self, collectorsdbMock):

    # Test with 0 rows modified as result

    collectorsdbMock.engineFactory.return_value = Mock(
      spec_set=sqlalchemy.engine.Engine)
    collectorsdbMock.engineFactory.return_value.execute.side_effect = (
      iter([Mock(rowcount=0), Mock()]))

    metric_utils.updateLastEmittedNonMetricSequence("twitter-tweets-volume", 0)

    # Assert that an update was called, followed by an insert
    args, _ = (collectorsdbMock
               .engineFactory
               .return_value
               .execute
               .call_args_list[0])
    self.assertTrue(args)
    self.assertIsInstance(args[0], sqlalchemy.sql.dml.Update)

    args, _ = (collectorsdbMock
               .engineFactory
               .return_value
               .execute
               .call_args_list[1])
    self.assertTrue(args)
    self.assertIsInstance(args[0], sqlalchemy.sql.dml.Insert)


    # Test again with 1 row modified as result

    collectorsdbMock.engineFactory.return_value.execute.reset_mock()

    collectorsdbMock.engineFactory.return_value.execute.side_effect = (
      iter([Mock(rowcount=1), Mock()]))

    metric_utils.updateLastEmittedNonMetricSequence("twitter-tweets-volume", 0)

    # Assert that an update was called, not followed by an insert
    args, _ = (collectorsdbMock
               .engineFactory
               .return_value
               .execute
               .call_args_list[0])
    self.assertTrue(args)
    self.assertIsInstance(args[0], sqlalchemy.sql.dml.Update)

    self.assertEqual(
      collectorsdbMock.engineFactory.return_value.execute.call_count, 1)


  @patch("taurus.metric_collectors.metric_utils.collectorsdb", autospec=True)
  def testUpdateLastEmittedSampleDatetime(self, collectorsdbMock):
    collectorsdbMock.engineFactory.return_value = Mock(
      spec_set=sqlalchemy.engine.Engine)

    metric_utils.updateLastEmittedSampleDatetime("twitter-tweets-volume",
                                                 datetime.utcnow())

    args, _ = (collectorsdbMock
               .engineFactory
               .return_value
               .execute
               .call_args_list[0])
    self.assertTrue(args)
    self.assertIsInstance(args[0], sqlalchemy.sql.dml.Update)


  @patch("taurus.metric_collectors.metric_utils.collectorsdb", autospec=True)
  def testQueryLastEmittedNonMetricSequence(self, collectorsdbMock):
    collectorsdbMock.engineFactory.return_value = Mock(
      spec_set=sqlalchemy.engine.Engine)

    metric_utils.queryLastEmittedNonMetricSequence("twitter-tweets-volume")

    args, _ = (collectorsdbMock
               .engineFactory
               .return_value
               .execute
               .call_args_list[0])
    self.assertTrue(args)
    self.assertIsInstance(args[0], sqlalchemy.sql.Select)


  @patch("taurus.metric_collectors.metric_utils.requests", autospec=True)
  def testUnMonitorMetric(self, requestsMock):

    requestsMock.delete.return_value = Mock(status_code=200)

    metric_utils.unmonitorMetric("localhost", "taurus", "foo")

    requestsMock.delete.assert_called_once_with(
      "https://localhost/_models/foo",
      verify=ANY, auth=("taurus", ""))


  @patch("taurus.metric_collectors.metric_utils.time.sleep", autospec=True)
  @patch("taurus.metric_collectors.metric_utils.requests", autospec=True)
  def testUnMonitorMetricWithErrors(self, requestsMock, _sleepMock):

    requestsMock.delete.return_value = Mock()

    self.assertRaises(
      metric_utils.RetriesExceededError,
      metric_utils.unmonitorMetric, "localhost", "taurus", "foo"
    )

    requestsMock.delete.assert_called_with(
      "https://localhost/_models/foo",
      verify=ANY, auth=("taurus", ""))


  @patch(("taurus.metric_collectors.metric_utils.message_bus_connector"
          ".MessageBusConnector"), autospec=True)
  def testMetricDataBatchWrite(self, messageBusConnectorClassMock):

    samples = [
      ("FOO.BAR.%d" % i, i * 3.789, i * 300)
      for i in xrange((metric_utils._METRIC_DATA_BATCH_WRITE_SIZE * 3) / 2)
    ]

    messageBusConnectorClass = (
      metric_utils.message_bus_connector.MessageBusConnector)
    messageBusMock = MagicMock(
      spec_set=messageBusConnectorClass,
      publish=Mock(spec_set=messageBusConnectorClass.publish))
    messageBusMock.__enter__.return_value = messageBusMock

    messageBusConnectorClassMock.return_value = messageBusMock

    loggerMock = Mock(spec_set=logging.Logger)
    with metric_utils.metricDataBatchWrite(loggerMock) as putSample:
      # put enough for the first batch
      for sample in samples[:metric_utils._METRIC_DATA_BATCH_WRITE_SIZE]:
        putSample(*sample)

      # The first publish call should be for a full batch
      self.assertEqual(messageBusMock.publish.call_count, 1)
      call0 = mock.call(
        mqName="taurus.metric.custom.data",
        persistent=True,
        body=json.dumps(
          dict(
            protocol="plain",
            data=["%s %r %d" % (m, v, t)
                  for m, v, t
                  in samples[:metric_utils._METRIC_DATA_BATCH_WRITE_SIZE]])))
      self.assertEqual(messageBusMock.publish.call_args_list[0], call0)

      # put the remaining samples
      for sample in samples[metric_utils._METRIC_DATA_BATCH_WRITE_SIZE:]:
        putSample(*sample)

      # the remaining incomplete batch will be sent upon exit from the context,
      # but not yet
      self.assertEqual(messageBusMock.publish.call_count, 1)

    # Now, the remainder should be sent, too
    self.assertEqual(messageBusMock.publish.call_count, 2)
    call1 = mock.call(
      mqName="taurus.metric.custom.data",
      persistent=True,
      body=json.dumps(
        dict(
          protocol="plain",
          data=["%s %r %d" % (m, v, t)
                for m, v, t
                in samples[metric_utils._METRIC_DATA_BATCH_WRITE_SIZE:]])))
    self.assertEqual(messageBusMock.publish.call_args_list[1], call1)



class CompanyDeleterTestCase(unittest.TestCase):


  @patch("taurus.metric_collectors.metric_utils.collectorsdb.engineFactory",
         autospec=True)
  @patch("taurus.metric_collectors.metric_utils.CompanyDeleter"
         "._flushTaurusEngineMetricDataPath",
         spec_set=metric_utils.CompanyDeleter._flushTaurusEngineMetricDataPath)
  @patch("taurus.metric_collectors.metric_utils.getAllMetricSecurities",
         autospec=True)
  @patch("taurus.metric_collectors.metric_utils.getAllCustomMetrics",
         autospec=True)
  @patch("taurus.metric_collectors.metric_utils.deleteMetric",
         autospec=True)
  def testDeleteCompanies(self,
                          deleteMetricMock,
                          getAllCustomMetricsMock,
                          getAllMetricSecuritiesMock,
                          _flushTaurusEngineMetricDataPathMock,
                          engineFactoryMock):
    negatives = set([
      "TWITTER.TWEET.HANDLE.ZZZ.VOLUME",
      "XIGNITE.ZZZ.CLOSINGPRICE",
      "XIGNITE.FOOBARZZZ.CLOSINGPRICE",
      "XIGNITE.ZZZFOOBAR.CLOSINGPRICE",
      "XIGNITE.FOOBAR.ZZZ.VOLUME",
      "XIGNITE.NEWS.FOOBAR.ZZZ.VOLUME",
      "FOOBAR.VOLUME",
      ".FOOBAR.CLOSINGPRICE",
      "XIGNITE.FOOBAR.",
      "FOOBARCLOSINGPRICE",
    ])

    positives = set([
      "XIGNITE.FOOBAR.CLOSINGPRICE",
      "XIGNITE.FOOBAR.VOLUME",
      "TWITTER.TWEET.HANDLE.FOOBAR.VOLUME",
      "XIGNTE.NEWS.FOOBAR.VOLUME",
      "XIGNITE.DOLITTLE.VOLUME",
    ])

    # Patch getAllCustomMetrics to return all negatives and positives
    getAllCustomMetricsMock.return_value = [
      {"name": metric} for metric in negatives.union(positives)
    ]

    # Simulate xitgnite_security found for first symbol, but not the second one.
    engineFactoryMock.return_value.begin.return_value.__enter__.return_value \
      .execute.side_effect = [Mock(rowcount=1), Mock(rowcount=0)]

    getAllMetricSecuritiesMock.return_value = [
      ("IBM", "exg"),
      ("T", "exg")
    ]

    # Execute the function under test
    metric_utils.CompanyDeleter.deleteCompanies(
      tickerSymbols=("FOOBAR", "DOLITTLE"),
      engineServer="host",
      engineApiKey="apikey",
      warnAboutDestructiveAction=False)

    # Verify that deleteMetric was called only on the positives
    expectedDeleteMetricCalls = [
      mock.call(host="host", apiKey="apikey", metricName=metric)
      for metric in positives
    ]

    self.maxDiff = None
    self.assertItemsEqual(deleteMetricMock.call_args_list,
                          expectedDeleteMetricCalls)

    self.assertEqual(engineFactoryMock.return_value.begin.return_value
                     .__enter__.return_value.execute.call_count, 2)



  @patch("taurus.metric_collectors.metric_utils.collectorsdb.engineFactory",
         autospec=True)
  @patch("taurus.metric_collectors.metric_utils.CompanyDeleter"
         "._flushTaurusEngineMetricDataPath",
         spec_set=metric_utils.CompanyDeleter._flushTaurusEngineMetricDataPath)
  @patch("taurus.metric_collectors.metric_utils.CompanyDeleter"
         "._warnAboutDestructiveAction",
         spec_set=metric_utils.CompanyDeleter._warnAboutDestructiveAction)
  @patch("taurus.metric_collectors.metric_utils.getAllMetricSecurities",
         autospec=True)
  @patch("taurus.metric_collectors.metric_utils.getAllCustomMetrics",
         autospec=True)
  @patch("taurus.metric_collectors.metric_utils.deleteMetric",
         autospec=True)
  def testDeleteCompaniesWithWarningConfirmation(
      self,
      deleteMetricMock,
      getAllCustomMetricsMock,
      getAllMetricSecuritiesMock,
      warnAboutDestructiveActionMock,
      _flushTaurusEngineMetricDataPathMock,
      engineFactoryMock):

    negatives = set([
      "TWITTER.TWEET.HANDLE.ZZZ.VOLUME",
    ])

    positives = set([
      "XIGNITE.FOOBAR.CLOSINGPRICE",
    ])

    # Patch getAllCustomMetrics to return all negatives and positives
    getAllCustomMetricsMock.return_value = [
      {"name": metric} for metric in negatives.union(positives)
    ]

    engineFactoryMock.return_value.begin.return_value.__enter__.return_value \
      .execute.return_value.rowcount = 1

    getAllMetricSecuritiesMock.return_value = [
      ("IBM", "exg"),
      ("T", "exg")
    ]

    # Execute the function under test with default warnAboutDestructiveAction
    metric_utils.CompanyDeleter.deleteCompanies(
      tickerSymbols=("FOOBAR", "DOLITTLE"),
      engineServer="host",
      engineApiKey="apikey")

    # Verify that _warnAboutDestructiveAction was called
    self.assertEqual(warnAboutDestructiveActionMock.call_count, 1)

    # Verify that deleteMetric was called only on the positives
    expectedDeleteMetricCalls = [
      mock.call(host="host", apiKey="apikey", metricName=metric)
      for metric in positives
    ]

    self.maxDiff = None
    self.assertItemsEqual(deleteMetricMock.call_args_list,
                          expectedDeleteMetricCalls)

    self.assertEqual(engineFactoryMock.return_value.begin.return_value
                     .__enter__.return_value.execute.call_count, 1)


  @patch("taurus.metric_collectors.metric_utils.CompanyDeleter"
         "._warnAboutDestructiveAction",
         spec_set=metric_utils.CompanyDeleter._warnAboutDestructiveAction)
  def testDeleteCompaniesWithWarningRejection(self,
                                              warnAboutDestructiveActionMock):

    warnAboutDestructiveActionMock.side_effect = (
      metric_utils.UserAbortedOperation)

    # Execute the function under test with default warnAboutDestructiveAction
    with self.assertRaises(metric_utils.UserAbortedOperation):
      metric_utils.CompanyDeleter.deleteCompanies(
        tickerSymbols=("FOOBAR", "DOLITTLE"),
        engineServer="host",
        engineApiKey="apikey")

    # Verify that _warnAboutDestructiveAction was called
    self.assertEqual(warnAboutDestructiveActionMock.call_count, 1)


  @patch("taurus.metric_collectors.metric_utils.CompanyDeleter"
         "._warnAboutDestructiveAction",
         spec_set=metric_utils.CompanyDeleter._warnAboutDestructiveAction)
  def testDeleteCompaniesWithWarningTimeout(self,
                                            warnAboutDestructiveActionMock):

    warnAboutDestructiveActionMock.side_effect = (
      metric_utils.WarningPromptTimeout)

    # Execute the function under test with default warnAboutDestructiveAction
    with self.assertRaises(metric_utils.WarningPromptTimeout):
      metric_utils.CompanyDeleter.deleteCompanies(
        tickerSymbols=("FOOBAR", "DOLITTLE"),
        engineServer="host",
        engineApiKey="apikey")

    # Verify that _warnAboutDestructiveAction was called
    self.assertEqual(warnAboutDestructiveActionMock.call_count, 1)


  @patch("taurus.metric_collectors.metric_utils.CompanyDeleter"
         "._waitForFlusherAndGarbageCollect",
         spec_set=metric_utils.CompanyDeleter._flushTaurusEngineMetricDataPath)
  @patch("taurus.metric_collectors.metric_utils.metricDataBatchWrite",
         autospec=True)
  def testFlushTaurusEngineMetricDataPath(self,
                                          metricDataBatchWriteMock,
                                          waitForFlusherAndGarbageCollectMock):

    metric_utils.CompanyDeleter._flushTaurusEngineMetricDataPath(
      engineServer="host",
      engineApiKey="apikey")

    # Verity putSample called
    self.assertEqual(metricDataBatchWriteMock.return_value.__enter__ \
                     .return_value.call_count, 1)

    # Verify _waitForFlusherAndGarbageCollect call
    waitForFlusherAndGarbageCollectMock.assert_called_once_with(
      engineServer="host",
      engineApiKey="apikey",
      flusherMetricName=ANY)


  @patch("taurus.metric_collectors.metric_utils.time.sleep", autospec=True)
  @patch("taurus.metric_collectors.metric_utils.getAllCustomMetrics",
         autospec=True)
  @patch("taurus.metric_collectors.metric_utils.deleteMetric",
         autospec=True)
  def testWaitForFlusherAndGarbageCollect(self,
                                          deleteMetricMock,
                                          getAllCustomMetricsMock,
                                          _timeSleepMock):
    oldFlusherMetricName = (
      metric_utils.CompanyDeleter._DATA_PATH_FLUSHER_METRIC_PREFIX + "0")

    flusherMetricName = (
      metric_utils.CompanyDeleter._DATA_PATH_FLUSHER_METRIC_PREFIX + "1")

    getAllCustomMetricsResultGroups = [
      [
        {"name": "XIGNITE.FOOBAR.CLOSINGPRICE"}
      ],

      [
        {"name": "XIGNITE.FOOBAR.CLOSINGPRICE"},

        {"name": oldFlusherMetricName}
      ],

      [
        {"name": "XIGNITE.FOOBAR.CLOSINGPRICE"},

        {"name": flusherMetricName}
      ],
    ]

    # Patch getAllCustomMetrics to return all negatives and positives
    getAllCustomMetricsMock.side_effect = iter(getAllCustomMetricsResultGroups)

    # Execute
    metric_utils.CompanyDeleter._waitForFlusherAndGarbageCollect(
      engineServer="host",
      engineApiKey="apikey",
      flusherMetricName=flusherMetricName)

    # Validate

    self.assertEqual(getAllCustomMetricsMock.call_count,
                     len(getAllCustomMetricsResultGroups))

    expectedDeleteMetricCalls = [
      mock.call(host="host", apiKey="apikey", metricName=oldFlusherMetricName),
      mock.call(host="host", apiKey="apikey", metricName=flusherMetricName)
    ]

    self.assertSequenceEqual(deleteMetricMock.mock_calls,
                             expectedDeleteMetricCalls)


  @patch("time.sleep", autospec=True)
  @patch("time.time", autospec=True)
  @patch("taurus.metric_collectors.metric_utils.getAllCustomMetrics",
         autospec=True)
  def testWaitForFlusherAndGarbageCollectWithFlusherNotFound(
      self,
      getAllCustomMetricsMock,
      timeMock,
      sleepMock):

    time_test_utils.configureTimeAndSleepMocks(timeMock, sleepMock)

    flusherMetricName = (
      metric_utils.CompanyDeleter._DATA_PATH_FLUSHER_METRIC_PREFIX + "1")


    # Patch getAllCustomMetrics to return all negatives and positives
    getAllCustomMetricsMock.return_value = [
      {"name": "XIGNITE.FOOBAR.CLOSINGPRICE"}
    ]

    # Execute and validate
    with self.assertRaises(metric_utils.FlusherMetricNotFound):
      metric_utils.CompanyDeleter._waitForFlusherAndGarbageCollect(
        engineServer="host",
        engineApiKey="apikey",
        flusherMetricName=flusherMetricName)


  @patch("__builtin__.raw_input", autospec=True)
  @patch("taurus.metric_collectors.metric_utils.random.randint", autospec=True)
  def testWarnAboutDestructiveActionConfirmed(self, randintMock, rawInputMock):
    randintMock.return_value = 1
    rawInputMock.return_value = "Yes-1"

    metric_utils.CompanyDeleter._warnAboutDestructiveAction(timeout=10,
                                                            tickerSymbols="FOO",
                                                            engineServer="host")

    self.assertEqual(rawInputMock.call_count, 1)


  @patch("__builtin__.raw_input", autospec=True)
  def testWarnAboutDestructiveActionRejected(self, rawInputMock):
    # NOTE: rejection can be anything other than the expected input of
    # "Yes-<randint>"
    rawInputMock.return_value = "No"

    with self.assertRaises(metric_utils.UserAbortedOperation):
      metric_utils.CompanyDeleter._warnAboutDestructiveAction(
        timeout=10,
        tickerSymbols="FOO",
        engineServer="host")


  @patch("__builtin__.raw_input", autospec=True)
  def testWarnAboutDestructiveActionTimedOut(self, rawInputMock):

    # NOTE: py.test by default captures console output and patches console input
    # such # that raw_input fails. Although not ideal, we have to patch
    # raw_input with something else that blocks and will be interrupted by
    # SIGINT.
    rawInputMock.side_effect = lambda *args: time.sleep(10)

    with self.assertRaises(metric_utils.WarningPromptTimeout):
      metric_utils.CompanyDeleter._warnAboutDestructiveAction(
        timeout=0.001,
        tickerSymbols="FOO",
        engineServer="host")



if __name__ == "__main__":
  unittest.main()
