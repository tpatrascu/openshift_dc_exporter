# OpenShift DeploymentConfig state Prometheus exporter

Prometheus exporter for OpenShift DeploymentConfig object state compatible with kube-state-metrics

# Install instructions

## Install the template

```
oc process -f dc-exporter-openshift-tpl.yaml | oc -n hawkular-exporter apply -f -
```

## Add view permission to the service account on the projects you want to collect data from

```
oc -n myproject policy add-role-to-user view system:serviceaccount:myproject:dc-exporter
```