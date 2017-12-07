# OpenShift DeploymentConfig state Prometheus exporter

Prometheus exporter for OpenShift DeploymentConfig object state compatible with kube-state-metrics

# Install instructions

## Install the template

You can specify multiple projects to collect as a space separated list:

```
oc process -f dc-exporter-openshift-tpl.yaml -p COLLECT_PROJECTS="myproject" | oc -n myproject apply -f -
```

## Add view permission to the service account on the projects you want to collect data from

```
oc -n myproject policy add-role-to-user view system:serviceaccount:myproject:dc-exporter
```
