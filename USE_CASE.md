<!--
Copyright 2015 F5 Networks Inc.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

  http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
-->
#f5-cccl

##Introduction

The Common Core Controller Library (CCCL) is an orchestration library that
provides a declarative API for defining BIG-IP LTM services in diverse
environments (e.g. Marathon, Kubernetes, OpenStack).  The API will allow a user
to create proxy services by specifying the: virtual servers, pools and members,
L7 policy and rules, and monitors as a service description object.  Each
instance of the CCCL is initialized with namespace qualifiers to allow it to
uniquely identify the resources under its control.

###Design Guidelines:

The CCCL will only manage the following resources: virtual servers, pools, pool
members, health monitors, and L7 policy and rules encapsulated in a service
object.  This is defined in the CCCL API schema and will be configured as iApps.
There is a one to one relationship between a service and a virtual server.

* The CCCL will accept a list of services to assure; however, it will not manage dependencies among these services.
* The CCCL manages one and only one BIG-IP partition.  If multiple partitions need to be managed, then extra instances of the CCCL need to be created.
* The CCCL API is declarative, meaning that every call to the CCCL provides the entire configuration as it should be deployed on the BIG-IP partition.
* The CCCL API is idempotent, meaning that successive calls to the CCCL with the same inputs result in the same partition configuration, and that there are no side effects.
* The CCCL is stateless and does not maintain persistent store of services.

###Use Cases

For the discussion services are composed of a virtual server, pools, members,
health monitors and content switching rules.

1. Multiple independent services.
* This is the basic use case.  A virtual server defined in a given service owns
all the resources defined as part of the service definition.  Each service does
not share virtual address and node addresses.  All resources are defined within
the managed partition.  In addition to the resources that are defined as a part
of the service, each service may reference predefined resources such as
policies, SNAT pools, or iRules.
2. Multiple services with shared virtual address
* This is the case where the virtual servers defined in the service set have the
same destination address, but the service ports differ.  The virtual address is
removed when the last virtual server referencing it is deleted.
3. Multiple services with shared global virtual address.
* A VIP can be allocated from a shared network, in which case it must be defined
in the Common partition where is accessible across tenant partitions.  This use
case requires that the destination address be allocated in advance of deploying
any one service because no one partition can own the VIP.  The virtual address
object needs to be created in the /Common partition if it is allocated from a
shared network.
4. Multiple services with a shared pool
* For pools shared among listeners, one pool will be created in the tenant
partition.  Each virtual service will reference the same pool by name.  This
pool can be defined as a 'pool only' service.  If a pool with the same name is
defined in multiple services and the pool configurations are not in agreement,
an exception should be thrown before the configuration is applied.  It is
expected that the member addresses belong to a route domain defined in the
managed partition; otherwise, an exception is thrown.
5. Tiered services
* In this case a service defines content switching rules that target a resource
(e.g. a virtual server or pool) that is defined by another service.  This
complicates the task of applying configuration to a BIG-IP partition.  Because
there are relational dependencies, the order in which the services are applied,
updated and deleted matters.  This order is defined in design.

###Partition and Resource Management

The purpose of the CCCL is to manage LTM resources in a clearly defined
namespace on the BIG-IP.  Current Velcro controller implementations reserve a
partition and own that partition and all resources contained within it.  For
OpenStack, the controller creates multiple partitions, one per tenant, and
manages the networking and LTM objects within it.  Each instance of the CCCL
will be responsible for managing the LTM resources in one and only one BIG-IP
partition.  The CCCL does not manage the life cycle of a partition.  If a
controller must manage separate partitions on multiple BIG-IP devices, it must
allocate a separate instances of the CCCL for each BIG-IP-partition pair.  As
part of the CCCL initialization, each instance will get a BIG-IP SDK handle and
a partition to manage.

Currently, there is no need for the CCCL to manage services in the Common
partition.  However, should the need arise, there needs to be a way for each
CCCL instance to discriminate among the among the resources it owns and those
that are deployed by other controller instances.  For this purpose each CCCL
instance can prefix the name of the services it deploys into a partition with a
unique identifier.  This identifier can be either be a configurable string or an
auto generated unique ID that can be hash of predefined info (e.g. controller
host, partition, etc.)  Note: we may revisit this.

The resource types that the CCCL will manage are: virtual servers, pools, pool
members, health monitors, L7 policies and L7 policy rules.  These are defined
as a list of services by the cccl-api-schema, and will be collectively managed
on the BIG-IP within the managed partition.  This design CCCL will address the
individual management of these resources.  No networking objects are created as
part of the service configuration application – any network configuration that
the service depends upon must be managed outside of the CCCL.  

It is possible for a controller to create resources like virtual addresses and
nodes that the CCCL services depend upon.  Since both virtual addresses and
nodes are associated with a route domain, the CCCL will only manage those
resources associated with a route domain defined in the managed partition;
otherwise and exception will be thrown.

###CCCL API

####Service Definition Schema

A service object encapsulates all the necessary configuration for a virtual
server deployment.  [The schema for the CCCL is defined here](https://bldr-git.int.lineratesystems.com/velcro/cccl/raw/master/cccl-api-schema.json).  It is also
included as an attachment to this page.

The schema conforms to the JSON draft 4 standard.  All CCCL input services are
validated by a Draft 4 JSON validator, which is extended to include defaults.

An example service configuration would be:

```python
{
"services": [
{
"name": "test_iApp2",
"partition": "Project",
"virtualServer": {
"destinationAddress": "192.168.0.1",
"name": "vs1",
"port": 80,
"defaultPoolIndex": 0,
"routeDomain": {"id": 0 }
},
"pools": [
{ "name": "pool1",
"members": [
{"ipAddress": "172.16.0.100", "port": 8080, "routeDomain": 0},
{"ipAddress": "172.16.0.101", "port": 8080, "routeDomain": 0}
],
"monitors": [{ "monitorIndex": 0 }, { "monitorIndex": 1 }]
}
],
"monitors": [
{ "name": "/Common/http",
"protocol": "http",
"send": "GET /\r\n",
"recv": "SERVER" },
{ "name": "/Common/gateway_icmp",
"protocol": "gateway_icmp" }
],
"l7Policy": {
"name": "wrapper_policy",
"rules": [
{
"conditions": [
{"group": 0,
"operand": "http-uri-host",
"condition": "equals",
"value": "www.mysite.com"},
{"group": 0,
"operand": "http-uri-path",
"condition": "equals",
"value": "/foo"},
{"group": 1,
"operand": "http-uri-host",
"condition": "equals",
"value": "www.yoursite.com"},
{"group": 1,
"operand": "http-uri-path",
"condition": "equals",
"value": "/bar"}
],
"actions": [
{"group": 0, "action": "reject", "target": "www.yoursite.com"},
{"group": 1, "action": "forward-pool", "target": 0}
]
}
]
}
}
]
}
```

####F5CommonControllerLib

``` python
class F5CommonControllerLib:
"""F5 Common Controller Core Library

"""
def __init__(self, bigip, partition, prefix=None):
""" Initialize an instance of the CCCL.

:param bigip:  Interface to BIG-IP, f5.bigip.ManagementRoot.
:param partition: Name of BIG-IP partition to manage.
:param prefix: Name prefix for managed resources.
"""
self.bigip = bigip
self.partition = partition
self.prefix = prefix

def applyConfig(self, services):
"""Apply service configurations to the BIG-IP partition.

:param services: A serializable object that defines one or more services.
Its schema is defined by cccl-api-schema.json.

:return: True if successful, otherwise an F5CommonControllerLib exception is thrown.
"""
pass

def getStatus(self):
"""Gets status for each service in the managed partition.

:return: A serializable object of the statuses of each managed resource.
Its structure is defined by:
cccl-status-schema.json
"""
pass

def getStatistics(self):
"""Get statistics for each service in the managed partition.

:return: A serializable object of the virtual server statistics for each service.
Its structure is defined by:
cccl-statistics-schema.json
"""
pass
```

####Session Instantiation

Create a session object to manage requests between the controller and the BIG-IP
on the designated partition.

```python
ltmServicesManager = \
F5CommonControllerLib(
bigip,
partition,
prefix=None
)
```

Parameters:

- bigip - ManagementRoot object returned after establishing a connection to the BIG-IP.
- partition - The name of the BIG-IP partition to manage.
- prefix – An optional string to prepend to resource names.

Returns:

- A session that can be used to manage services on the supplied partition.

####Apply Config

Apply a list of service definitions to the managed BIG-IP partition.  The list
of service definitions represents the desired configuration state of the
partition upon completion.  This is a declarative method for configuration of
the BIG-IP.

```python
applyConfig(services)
```

Parameters:

- services – A list of services defined in a serializable object that conforms to the cccl-api-schema.

Returns:

- Nothing

Exceptions:

1. TODO: Exceptions to be defined:
2. ServiceSerialization error.
3. ServiceValidation error
4. InvalidConfiguration error.
5. PartitionAuthentication error.
6. ConfigApplication error.

The applyConfig operation accepts a set of services that represent the desired
state of the managed partition, let's call this set D.  After validating the
service input and applying the appropriate configuration checks to it, CCCL
queries the BIG-IP to get the existing set of services currently deployed in the
managed partition, let's call this set E.  Before applying a new configuration,
it first decides which services must be created, updated, and deleted on the
managed partition.  These services are defined as follows\:

> createSet = All services x, such that x belongs to D and x does not belong to E.
> updateSet = All services x, such that x belongs to D and x belongs to E, and the existing service state differs from the desired service.
> deleteSet = All services x, such that x does not belong to D and x belongs to E.

If the services are independent, the application of the configuration is
straightforward, the CCCL will perform creates, then modifies, then deletes.
The complication arise when the services have interdependencies.  It is very
possible to provide a set of services that cannot be satisfied, how to roll back
a half deployed configuration, or even how to report errors in the event this
occurs needs more investigation.

The table below demonstrates the state transitions on subsequent calls to the
cccl object:
| Time | applyConfig desired service | BIG-IP Partition State | Notes                             |
|------|-----------------------------|------------------------|-----------------------------------|
| 0    |                             | {}                     | Initially the partition is empty  |
| 1    | (A)                         | (A)                    | Add service A                     |
| 2    | (B)                         | (B)                    | Add service B; delete A           |
| 3    | ( )                         | ( )                    | Delete A, then B                  |
| 4    | (A, B)                      | (A, B)                 | Add A; add B                      |
| 5    | (A, B', C)                  | (A, B', C)             | Add C; update B                   |
| 6    | (B'', C', D)                | (B'', C', D)           | Add D; update B, then C; delete A |

Using the declarative interface requires that the controller component be able
to reconstruct the set of services each time the operation is invoked.  This is
necessary in the case where the controller crashes and services state needs to
be assured.

####Get Service Status

Get status of each managed resource in the partition.

```python
serviceStatus = getStatus()
```

Parameters:
* None
Returns:
* Service status dictionary based on cccl-status-schema.json

```python
{
"services": [
{
"name": "test_App2",
"virtualServer": {
"status": "online"
},
"pools": [
{
"name": "pool1",
"status": "online",
"members": [
{
"ipAddress": "172.16.0.100",
"status": "online"
},
{
"ipAddress": "172.16.0.101",
"status": "online"
}
]
}
],
"monitors": [
{
"name": "/Common/http",
"status": "online"
},
{
"name": "/Common/gateway_icmp",
"status": "online"
}
]
}
]
}
```
Exceptions: TBD

###CRUD Interface

A basic CRUD interface allows the controller to create, read, update, and
delete services individually.  This will not be implemented as part of the
initial implementation.  It might be implemented as an optimization.

####Create Service
```python
createService(service)
```

Add the provided service to the managed partition.

Parameters:

- service – A service defined in a JSON object that conforms to the cccl-api-schema.

Returns:

- Nothing

Exceptions:

- HTTP 400,
- HTTP 401,
- HTTP 409,
- HTTP 500

####Update Service
```python
updateService(service)
```
Update the provided service to the managed partition.  The service should exist
already.  The underlying operation is a PATCH on the existing service.  This
allows for an in place modification of service configuration.

Parameters:

- service – A service defined in a JSON object that conforms to the cccl-api-schema.

Returns:

- Nothing

Exceptions:

- HTTP 400,
- HTTP 401,
- HTTP 404,
- HTTP 500

####Delete Service

```python
deleteService(serviceName)
```

Delete the service named serviceName from the managed partition.  The service
should exist already.  The underlying operation is a DELETE on the existing
service.

Parameters:

- serviceName – A string name identifying the iApp service to delete.

Returns:

- Nothing

Exceptions:

- HTTP 400,
- HTTP 401,
- HTTP 404,
- HTTP 500

####Get Service

```python
service = getService(serviceName)
```

Retrieve the service named serviceName from the managed partition.  The service
should exist already.  The underlying operation is a GET on the existing
service.

Parameters:

- serviceName – A string name identifying the iApp service to delete.

Returns:

- An object representing the iApp in the managed partition.

Exceptions:

- HTTP 400,
- HTTP 401,
- HTTP 404,
- HTTP 500
Get Service Statistics TODO
Sequence Diagrams
