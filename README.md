# OpenShift DeploymentConfig state Prometheus exporter

Prometheus exporter for OpenShift DeploymentConfig object state compatible with kube-state-metrics

# Install instructions

Requires cluster-admin privilege to install.

```
oc process -f dc-exporter-openshift-tpl.yaml -p NAMESPACE=myprometheus | oc apply -f -
```
