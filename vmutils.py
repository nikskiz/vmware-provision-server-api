#! /usr/bin/python

import pyVim
import sys
from pyVim import connect
from pyVim.connect import SmartConnect, Disconnect
from pyVmomi import vim, vmodl
import Logger

def _get_obj(content, vimtype, name):
        #Get the vsphere object associated with a given text name
    obj = []
    container = content.viewManager.CreateContainerView(content.rootFolder, vimtype, True)
    for c in container.view:
        if c.name == name:
            obj = c
            break
        elif name == "":
            obj.append(c)
    return obj

def get_resource_pool(si, name):
        #Find a virtual machine by it's name and return it
    return _get_obj(si.RetrieveContent(), [vim.ResourcePool], name)

def get_datacenter_by_name(si, name):
    return _get_obj(si.RetrieveContent(), [vim.Datacenter], name)

def get_vm_by_name(si, name):
        # Find a virtual machine by it's name and return it
   return _get_obj(si.RetrieveContent(), [vim.VirtualMachine], name)

def get_host_by_name(si, name):
        #Find a virtual machine by it's name and return it
    return _get_obj(si.RetrieveContent(), [vim.HostSystem], name)

def get_cluster_by_name(si, name):
    return _get_obj(si.RetrieveContent(), [vim.ClusterComputeResource], name)

def get_folder_by_name(si, name):
    return _get_obj(si.RetrieveContent(), [vim.Folder], name)

def get_datastore_by_name(si, name):
    return _get_obj(si.RetrieveContent(), [vim.Datastore], name)

def get_network_by_name(si, name):
    return _get_obj(si.RetrieveContent(), [vim.Network], name)

def index_search(si, uid):
    vm = None
    search = si.RetrieveContent().searchIndex
    vm = search.FindByUuid(uuid=uid,vmSearch=True)
    return vm

def vm_disks(vm):
    disks = []
    devices = vm.config.hardware.device
    for device in devices:
        if isinstance(device, vim.vm.device.VirtualDisk):
            disks.append(device)
    return disks

def wait_for_task(task):
        #wait for a vCenter task to finish """
    task_done = False
    while not task_done:
        if task.info.state == 'success':
            Logger.logging.debug("DONE!")
            return task.info.result
        if task.info.state == 'error':
            Logger.logging.debug('ERROR: %s' % (task.info.error.msg))
            task_done = True
