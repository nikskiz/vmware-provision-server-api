#! /usr/bin/python
# Nikola Sepentulvski
import ssl
import pyVim
import sys
from pyVim import connect
from pyVim.connect import SmartConnect, Disconnect
from pyVmomi import vim, vmodl
import vmutils
import argparse
import getpass
import pycurl
import psycopg2
import operator
import Logger

def Connect(user, pwd):
    try:
        context = ssl.SSLContext(ssl.PROTOCOL_SSLv23)
        context.verify_mode = ssl.CERT_NONE
        si = connect.SmartConnect(host="gsx-0001vmm.server-login.com", user=user, pwd=pwd, sslContext=context)

    except:
        print("Failed to login!")
        sys.exit()
    else:
        return si

def choose_datastore(si):
    avail_datastore = { }
    datastores = vmutils.get_datastore_by_name(si, "")
    for datastore in datastores:
        if "VPS" in datastore.name:
            ## Find a datastore with the most availavle storage
            avail_datastore.update({datastore.summary.name: datastore.summary.freeSpace})

    # Return the datastore with the max freespace
    available_datastore = max(avail_datastore.iteritems(), key=operator.itemgetter(1))[0]
    return available_datastore


# Get Company ID based on the greencode Arg
def get_company_id(greencode):
    conn = psycopg2.connect("dbname='automation' user='a2user' host='console-db-archive.private.netregistry.net' password='cUntbItch'")
    cur = conn.cursor()
    cur.execute("select company_id from company where greencode ='"+greencode+"'")
    for company_id in cur:
        for cid in company_id:
            return cid
    conn.close()


### Function to login to the console
def console_login():
    curl = pycurl.Curl()
    # Login
    curl.setopt(pycurl.URL, "***")
    curl.setopt(pycurl.SSL_VERIFYPEER, 0)
    curl.setopt(pycurl.COOKIEJAR, 'cookie.txt')
    curl.setopt(pycurl.POST, 1)
    curl.setopt(pycurl.POSTFIELDS, '******')
    curl.setopt(pycurl.WRITEFUNCTION, lambda x: None)
    curl.perform()

# Add VPS in the Console
def console_add_vps(company_id,vname,vname_uid,osId):
    curl = pycurl.Curl()
    curl.setopt(pycurl.URL, "******")
    curl.setopt(pycurl.SSL_VERIFYPEER, 0)
    curl.setopt(pycurl.COOKIEFILE, 'cookie.txt')
    curl.setopt(pycurl.POST, 0)
    curl.setopt(pycurl.WRITEFUNCTION, lambda x: None)
    curl.setopt(pycurl.POSTFIELDS, 'osId='+osId+'&machineName='+vname+'******')
    curl.perform()

def main(vps_name, vps_product, folder, template_vm_uid):
    user = '***'
    pwd = '****'
    # Connect to vsphere
    si =  Connect(user, pwd)

    # Define hotadd default options
    chotadd = True
    mhotadd = True

    if vps_product == "vps1":
        ncpu = 2
        npsocket = 2
        mem = 1024
    elif vps_product == "vps2":
        ncpu = 2
        npsocket = 2
        mem = 2048
    elif vps_product == "vps4":
        ncpu = 4
        npsocket = 2
        mem = 4096
    elif vps_product == "vps8":
        ncpu = 4
        npsocket = 2
        mem = 8192

    datacenter = vmutils.get_datacenter_by_name(si, "Global Switch")
    Logger.logging.debug("Using Datacenter: %s" % (datacenter.name))

    # Search for the vm and return the object. This case we are looking for a Template.
    template_vm = vmutils.index_search(si, template_vm_uid)
    Logger.logging.debug("Using VM Teamplate: %s" % (template_vm_uid))
    Logger.logging.debug("Using VM Teamplate: %s" % (template_vm.name))

    # Search for folder location
    destfolder = vmutils.get_folder_by_name(si, folder)
    Logger.logging.debug("Using Folder: %s" % (destfolder.name))

    # Search for the cluster and return the clust object, which is also used to get the resource pool
    cluster = vmutils.get_cluster_by_name(si, '******')
    # Get the root resource pool in the cluster (root resource pool does not limit the resources)
    for pool in cluster.resourcePool.resourcePool:
        if pool.name == "Root":
	   resourcepool = pool
    Logger.logging.debug("Using Resource Pool %s in Cluster %s" % (resourcepool.name, cluster.name))

    # Search for datastore and find datastore that has the most available disk space
    get_free_datastore = choose_datastore(si)
    datastore = vmutils.get_datastore_by_name(si, get_free_datastore)
    #print datastore.name
    #sys.exit()
    Logger.logging.debug("Using Datastore: %s" % (datastore.name))

    ### Configur VM ###

    Logger.logging.debug("Configuring VM")
    relospec = vim.vm.RelocateSpec()
    # Apply datastore
    relospec.datastore = datastore
    # Apply Cluster/ResourcePool
    relospec.pool = resourcepool
    # Thin Provision Disk
    relospec.transform = vim.vm.RelocateSpec.Transformation.sparse


    # Define Mem Config
    vmconf = vim.vm.ConfigSpec()
    vmconf.memoryMB = mem
    # Define Number of virtual processors
    vmconf.numCPUs = ncpu
    # Number of cores among which to distribute CPUs in this virtual machine
    vmconf.numCoresPerSocket = npsocket
    #Whether more CPU can be added while virtual machine is powered on (Hot Add)
    vmconf.cpuHotAddEnabled = chotadd
    #Whether more Mem can be added while Virtual machine is powered on (hot Ddd)
    vmconf.memoryHotAddEnabled = mhotadd

    # Network adapter settings
    adaptermap = vim.vm.customization.AdapterMapping()
    adaptermap.adapter = vim.vm.customization.IPSettings(ip=vim.vm.customization.DhcpIpGenerator(), dnsDomain='******')

    # static ip
    adaptermap.adapter = vim.vm.customization.IPSettings(ip=vim.vm.customization.FixedIp(ipAddress='***'),
                                                     subnetMask='****', gateway='****')
    # for static ip
    globalip = vim.vm.customization.GlobalIPSettings(dnsServerList=['***', '****'])

    # Hostname settings
    ident = vim.vm.customization.LinuxPrep(domain='****8', hostName=vim.vm.customization.FixedName(name=vps_name))

    # Putting all these pieces together in a custom spec
    customspec = vim.vm.customization.Specification(nicSettingMap=[adaptermap], globalIPSettings=globalip, identity=ident)

    # Clone spec
    clonespec = vim.vm.CloneSpec()
    clonespec.location = relospec
    clonespec.config = vmconf
    clonespec.customization = customspec

    # Power On VM
    clonespec.powerOn = True
    clonespec.template = False


    task = template_vm.Clone(folder=destfolder, name=vps_name, spec=clonespec)
    Logger.logging.debug("cloning VM...")
    result = vmutils.wait_for_task(task)
    if result is not None:
        Logger.logging.debug("The VM UID is: %s" % (result.config.uuid))
        vname_uid = str(result.config.uuid)

    return vname_uid

    Disconnect(si)

if __name__ == "__main__":
    main()
