#!/usr/bin/env python3

from openshift import client, config
from prometheus_client import start_http_server
from prometheus_client.core import GaugeMetricFamily, CounterMetricFamily, REGISTRY
import os
import time
import math
import argparse
from collections import OrderedDict

EXPORTER_NAMESPACE = 'kube_'
EXPORTER_PORT = 8000

parser = argparse.ArgumentParser(description='Prometheus exporter for OpenShift DeploymentConfig state.')
parser.add_argument('-projects', metavar='project', type=str, required=True, nargs='+',
                     help='list of projects to collect')
args = parser.parse_args()

if 'KUBERNETES_PORT' not in os.environ:
    config.load_kube_config()
else:
    config.load_incluster_config()

oapi = client.OapiApi()

def get_max_unavailable(int_or_percent, total):
    if int_or_percent.find('%') != -1:
        return math.ceil(total * int(int_or_percent[:-1]) / 100)
    else:
        return int_or_percent

class DCCollector(object):
    def collect(self):
        for namespace in args.projects:
            for dc in oapi.list_namespaced_deployment_config(namespace).items:
                dc_status = oapi.read_namespaced_deployment_config_status(dc.metadata.name, namespace)

                dc_metrics = {
                    'deployment_created': 0 if dc.metadata.creation_timestamp == 0 else 1,
                    'deployment_metadata_generation': dc.metadata.generation,
                    'deployment_spec_paused': 1 if dc.spec.paused else 0,
                    'deployment_spec_replicas': dc.spec.replicas,
                    'deployment_status_observed_generation': dc_status.status.observed_generation,
                    'deployment_status_replicas': dc_status.status.replicas,
                    'deployment_status_replicas_available': dc_status.status.available_replicas,
                    'deployment_status_replicas_unavailable': dc_status.status.unavailable_replicas,
                    'deployment_status_replicas_updated': dc_status.status.updated_replicas,
                }

                metric_labels = ['namespace', 'deployment']

                for metric_name, metric_value in dc_metrics.items():
                    metric_family = GaugeMetricFamily(
                        EXPORTER_NAMESPACE + metric_name,
                        '',
                        labels=metric_labels
                    )
                    metric_family.add_metric([namespace, dc.metadata.name], metric_value)
                    yield metric_family
                
                dc_meta_labels = OrderedDict(dc.metadata.labels)
                metric_family = GaugeMetricFamily(
                    EXPORTER_NAMESPACE + 'deployment_labels',
                    'Kubernetes labels converted to Prometheus format',
                    labels=metric_labels + ['label_{}'.format(x) for x in dc_meta_labels.keys()]
                )
                metric_family.add_metric(
                    [namespace, dc.metadata.name] + list(dc_meta_labels.values()), 1)
                yield metric_family

                if dc.spec.strategy.type == 'Rolling':
                    max_unavailable = get_max_unavailable(
                        dc.spec.strategy.rolling_params.max_unavailable,
                        dc_status.status.replicas
                    )

                    metric_family = GaugeMetricFamily(
                        EXPORTER_NAMESPACE + 'deployment_spec_strategy_rollingupdate_max_unavailable',
                        '',
                        labels=metric_labels
                    )
                    metric_family.add_metric([namespace, dc.metadata.name], max_unavailable)
                    yield metric_family


if __name__ == "__main__":
    start_http_server(EXPORTER_PORT)
    print('Listening on port {}'.format(EXPORTER_PORT))
    REGISTRY.register(DCCollector())
    while True: time.sleep(1)
