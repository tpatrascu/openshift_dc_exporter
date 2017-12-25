#!/usr/bin/env python

from openshift import client, config

from prometheus_client import start_http_server
from prometheus_client.core import GaugeMetricFamily, CounterMetricFamily, REGISTRY

from collections import OrderedDict
import os
import time
import math

EXPORTER_NAMESPACE = 'kube_'
EXPORTER_PORT = 8080


class DCCollector(object):
    def collect(self):
        for dc in oapi.list_deployment_config_for_all_namespaces().items:
            dc_status = oapi.read_namespaced_deployment_config_status(dc.metadata.name, dc.metadata.namespace)

            dc_metrics = {
                'deployment_created': time.mktime(dc.metadata.creation_timestamp.timetuple()),
                'deployment_metadata_generation': dc.metadata.generation,
                'deployment_spec_paused': 1 if dc.spec.paused else 0,
                'deployment_spec_replicas': dc.spec.replicas,
                'deployment_status_observed_generation': dc_status.status.observed_generation,
                'deployment_status_replicas': dc_status.status.replicas,
                'deployment_status_replicas_available': dc_status.status.available_replicas,
                'deployment_status_replicas_unavailable': dc_status.status.unavailable_replicas,
                'deployment_status_replicas_updated': dc_status.status.updated_replicas,
            }

            default_metric_labels = ['namespace', 'deployment']

            for metric_name, metric_value in dc_metrics.items():
                metric_family = GaugeMetricFamily(
                    EXPORTER_NAMESPACE + metric_name,
                    '',
                    labels=default_metric_labels
                )
                metric_family.add_metric([dc.metadata.namespace, dc.metadata.name], metric_value)
                yield metric_family


# TODO: fix this
#            dc_meta_labels = OrderedDict(dc.metadata.labels)
#            metric_family = GaugeMetricFamily(
#                EXPORTER_NAMESPACE + 'deployment_labels',
#                'Kubernetes labels converted to Prometheus format',
#                labels=default_metric_labels + ['label_{}'.format(x.replace('-', '_')) for x in dc_meta_labels.keys()]
#            )
#            metric_family.add_metric(
#                [dc.metadata.namespace, dc.metadata.name] + list(dc_meta_labels.values()), 1)
#            yield metric_family


            if dc.spec.strategy.type == 'Rolling':
                max_unavailable = dc.spec.strategy.rolling_params.max_unavailable
                # if rolling_params.max_unavailable is specified as percent, compute nr of pods
                if max_unavailable.find('%') != -1:
                    max_unavailable = math.ceil(dc_status.status.replicas * int(max_unavailable[:-1]) / 100)

                metric_family = GaugeMetricFamily(
                    EXPORTER_NAMESPACE + 'deployment_spec_strategy_rollingupdate_max_unavailable',
                    '',
                    labels=default_metric_labels
                )
                metric_family.add_metric([dc.metadata.namespace, dc.metadata.name], max_unavailable)
                yield metric_family


if __name__ == "__main__":
    if 'KUBERNETES_PORT' not in os.environ:
        config.load_kube_config()
    else:
        config.load_incluster_config()

    oapi = client.OapiApi()

    start_http_server(EXPORTER_PORT)
    print('Listening on port {}'.format(EXPORTER_PORT))
    REGISTRY.register(DCCollector())
    while True: time.sleep(1)
