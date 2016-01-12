===============================
Tenant based backup and restore
===============================

Blueprint URL:
- https://blueprints.launchpad.net/freezer/+spec/tenant-backup

Problem description
===================
As a tenant, I need to use Freezer to backup all my data and metadata from an OS Cloud and restore it
at my convenience. With this approach all the data can be restored on the same Cloud platform (in case anything went lost) or on an independent cloud (i.e. a new one freshly deployed on a different geographic location). 

Tenants needs to backup selectively all their resources from a the OS services.
These resources/services are:

- Users [meta]data stored in keystone (email, tenants)
- VMs in Nova
- Volumes in Cinder
- Objects in Swift
- Images in Glance
- Networks and other settings as FWaaS, LBaaS, VPNaaS in Neutron

Proposed change
===============

Backup Work Items
-----------------
For tenants backup the data and metadata needs to be retrieved from the services API, such as:

- Keystone:
    - Retrieve all the user data from the keystone API in json format
    - Download and backup the data in stream using the Freezer backup block based incremental, tenant mode

- Nova:
    - Retrieve the list of VMs of the tenant from the Nova API

    For each VM:
        - Save the metadata
        - Create a vm snapshot
        - Generate an image from a snapshot
        - Download the image file and process it in stream using the Freezer backup block based incremental, tenant mode
        - Remove the image and the snapshot

- Cinder:
    - Retrieve the list of volumes of the tenant from the Cinder API

    For each Volume:
        - Save the metadata
        - Create a volume snapshot
        - Generate an image from snapshot
        - Download the image file and process it in stream using Freezer backup stream block based incremental tenant mode
        - Remove the image and the snapshot

- Swift (it make sense have Swift objects backup?):
    - Retrieve the list of containers from Swift
    - For each container
        - Save the metadata
        - Download and backup all the object in the containers in stream using the Freezer backup stream block based incremental tenant mode

- Glance:
    - Retrieve all the image list owned by the user from the Glance API
    - Save the metadata
    - Download the image file and process it in stream using Freezer backup stream block based incremental tenant mode

- Neutron:
    - Retrieve all the sub services enabled in neutron such as:
        - FwaaS, VPNaaS, LBaaS
    - Retrieve all the existing networks and routing for the tenant
    - Download and backup all the network and routing data/metadata in stream using the Freezer backup stream block based incremental tenant mode
    - Same apply for FWaaS, LBaaS, VPNaaS

Restore Work Items
------------------
The restore process should consist on downloading the data from the media storage, decompress/decrypt,
process it and recreate to each server the settings/configuration as they were at backup point in time.

A distinction needs to be done for metadata and data (i.e. the metadata of the vm and the vm image file itself).
The metadata needs to be downloaded in full before restoring the tenant data, as is probably not possible to upload to the openstack api services partial or incomplete metadata when restoring.

When restoring, the order of the services/components to restore should be the following:

- Keystone:
  - Retrieve all meta data from the freezer media storage
  - Recreate all the metadata on the Keystone API endpoint
  - Upload any data (non metadata)

- Neutron:
  - Retrieve all meta data from the freezer media storage
  - Recreate all the metadata on the Neutron API endpoint
  - Upload any data (non metadata)

- Glance:
  - Retrieve all meta data from the freezer media storage
  - Recreate all the metadata on the Glance API endpoint
  - Upload any data (non metadata, i.e. image files)

- Cinder:
  - Retrieve all meta data from the freezer media storage
  - Recreate all the metadata on the Cinder API endpoint
  - Upload any data (non metadata, i.e. volumes)
  - Make sure the user/tenant that owns the volume si correct

- Nova:
  - Retrieve all meta data from the freezer media storage
  - Recreate all the metadata on the Nova API endpoint
  - Upload any data (non metadata, i.e. VMs)
  - Make sure networking, volumes and user/tenants are correct

- Swift (If Swift backup doesn't make sense, probably the restore is in the same situation.):
  - Retrieve all meta data from the freezer media storage
  - Recreate all the metadata and containers using the Swift API endpoint
  - Upload any data object to the containers
  - Update the metadata (acl, read only, etc)

Further questions and considerations:
- How would be configured the data input?

- How would be configure the tenant backup.

Currently path_to_backup is used as source of where the data is read from. For tenant based backups the data to be backed up
would be read from a stream. The challenge is to specify the input as stream and the tenant mode.

Possible options:

- Provide "stream" to path_to_backup rather than the file system path, and use tenant as backup mode.

- Create a new backup mode called stream (in this case, how to we then set the tenant backup mode?)

- We can add an additional option called data_input_type, setting the default to fs (file system) or stream and use tenant as backup mode

- When restoring, would probably good to recreate the tenant resources with a tenant name provided by the user (i.e. provided by Openstack environment variable like the OS_TENANT_NAME var). This has the advantage to recreate the resources with a different tenant in case is needed.

- Does the Cinder volumes needs to be attached to the VMs, in case they were when the backup was taken?

- How do we store the metadata of all the service? Any particular structure? Do we need to have freezer metadata on top of that to make easy the restore and to diplay the information from the web ui?

- If the admin user/role execute the backup, actions can be taken probably on all_tenants for services like Nova and Cinder.
  We need to take this in consideration for ALL_TENANTS backups.

- Freezer needs to make sure the tenant data is backed up in a consistent manner, therefore the snapshot
  of the resources (i.e. Volumes and VMs) needs to be taken in the shortest time windows as possible.
  How do we make this happen? At least for the first release this will probably be best effort
  (i.e. vms and volumes snapshots will happen in parallel). We need to evaluate if Job Session can help on this use case.

- If during the tenant backup, something went wrong, will the backup stop or keep executing?
  Do we have some service/data that even if the backup fail, the execution can proceed?

- Where the backups should be executed and by which Freezer component?
  The backup can be executed from any node (virtual, physical, being part or totally independent
  from the infrastructure(i.e. compute node, storage node or a totally detached and cloud independent node)
  The component that execute all these actions should probably be the freezer-agent.

Milestones
----------
Target Milestone for completion:
  Mitaka


Dependencies
============
- Block based incremental backups (needs to be impleted abastracted from the fs, as the same code can be reused also for other streams based backups).
- A new backup mode and incremental type needs to be defined.

