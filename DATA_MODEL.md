#Common Controller Core Library Data Model

The CCCL Data Model represents the internal translation (data and order of
operations on that data) from the CCCL schema to the BIG-IP data model. The
goals of the Data Model are:

- Map schema objects to BIG-IP resources and perform schema validation
- Communicate with a BIG-IP to determine its configuration
- Configure a BIG-IP to match the input schema in the most efficient and least invasive way possible
- Understand and manage dependencies between BIG-IP resources

##Dependencies

The first step to organizing the internal data model for CCCL is understanding
the dependencies between BIG-IP resources; however these dependencies are well
known and detailed below.

| Resource | Dependencies                                                                                 |
|----------|----------------------------------------------------------------------------------------------|
| Virtual Server | Profiles                                                                               |
|                | Pools                                                                                  |
|                | iRules                                                                                 |
|                | Policies                                                                               |
| Pool Member | Pool, Node (nodes are automatically created for pool members if they don't already exist) |
| Pool       | Monitors                                                                                   |
| Monitor    | None                                                                                       |
| iRule      | Can depend on anything because it is a script                                              |
| Policy     | Policies are comprised of Conditions and Actions, and Actions can depend upon:             |
|            | Pools                                                                                      |
|            | Nodes                                                                                      |
|            | Virtual Servers                                                                            |
| iApp       | iApps manage their own dependencies and are currently independent of any other configs     |

###Immutable Parameters

Certain parameters of BIG-IP resources are immutable; they can only be "changed"
by destroying and recreating the resource. The "name" and "partition" of all
resources are immutable, as are the "type" of Health Monitors, and "address" and
"port" of Pool Members. Basically, any parameter that is part of a resource's
path in the REST API tree is immutable.

##Order of Operations

The dependencies define the order in which resources can be created. updated,
and deleted. In general, resources will be created and updated from the "bottom
up" and destroyed from the "top down".

Retrieve collections of BIG-IP resources: Virtual Servers, Pools, Pool Members,
Monitors, Policies, and iApps

Compare existing BIG-IP resources and schema-based input and create lists of
resources to be created, updated and deleted

Create resources in the following order: Monitors, Pools, Pool Members, Virtual
Servers (minus Policies and iRules), Policies, and iApps

Update resources in the following order: Monitors, Pools, Pool Members, Virtual
Servers (apply Policies and iRules), Policies, and iApps

Delete resources in the following order: iApps, Virtual Servers, Policies,
Pools, Pool Members, Monitors

###Implementation

The CCCL shall use the existing F5 Python SDK for communicating with the BIG-IP
and managing BIG-IP resources.

###Error Handling
The CCCL will catch errors/exceptions and provide appropriate feedback depending
on the use case:

- When operator-controlled, CCCL shall provide feedback to the user that a configuration succeeded or failed. If failed, CCCL shall provide enough detail to help diagnose the problem.
- When operated within a long-running automated process, CCCL shall provide configurable logging for CCCL events

###Questions/Thoughts

1. Do we need to consider dependencies between services (e.g. Policy is a Virtual Server references the Virtual Server from another service)?
2. We need to be explicit in the schema about all resource attributes (e.g. Virtual Server "enabled/disabled"). 
3. How to handle an error during deployment to BIG-IP
 - Stop?
 - Continue (i.e. best effort)
 - Rollback?
 - Use of transactions.
