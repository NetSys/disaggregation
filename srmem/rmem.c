/*
 * A sample, extra-simple block driver. Updated for kernel 2.6.31.
 *
 * (C) 2003 Eklektix, Inc.
 * (C) 2010 Pat Patterson <pat at superpat dot com>
 * Redistributable under the terms of the GNU GPL.
 * Modified by Sangjin Han (sangjin@eecs.berkeley.edu) and Peter Gao (petergao@berkeley.edu)
 */

#include <linux/module.h>
#include <linux/moduleparam.h>
#include <linux/init.h>

#include <linux/kernel.h> /* printk() */
#include <linux/fs.h>     /* everything... */
#include <linux/errno.h>  /* error codes */
#include <linux/types.h>  /* size_t */
#include <linux/vmalloc.h>
#include <linux/genhd.h>
#include <linux/blkdev.h>
#include <linux/hdreg.h>
#include <linux/random.h>

#include <linux/time.h>
#include <linux/proc_fs.h>
#include <linux/seq_file.h>

MODULE_LICENSE("Dual BSD/GPL");

static int npages = 2048 * 1024; 
module_param(npages, int, 0); 

static int ndev = 1;
module_param(ndev, int, 0);

/*
 * We can tweak our hardware sector size, but the kernel talks to us
 * in terms of small sectors, always.
 */
#define KERNEL_SECTOR_SIZE 	512
#define SECTORS_PER_PAGE	(PAGE_SIZE / KERNEL_SECTOR_SIZE)
#define DEVICE_BOUND 100


/*
 * The internal representation of our device.
 */
struct rmem_device {
	unsigned long size;
	spinlock_t lock;
	u8 **data;
	struct gendisk *gd;
  int major_num;
};

struct rmem_device* devices[DEVICE_BOUND];




/*
 * Handle an I/O request.
 */
static void rmem_transfer(struct rmem_device *dev, sector_t sector,
		unsigned long nsect, char *buffer, int write) 
{
	int i;
	int page;
	int npage;

	if (sector % SECTORS_PER_PAGE != 0 || nsect % SECTORS_PER_PAGE != 0) {
		pr_err("incorrect align: %lu %lu %d\n", sector, nsect, write);
		return;
	}

	page = sector / SECTORS_PER_PAGE;
	npage = nsect / SECTORS_PER_PAGE;

	if (page + npage - 1 >= npages) {
		printk (KERN_NOTICE "rmem: Beyond-end write (%d %d %d)\n", page, npage, npages);
		return;
	}


	if (write) {
		
		for (i = 0; i < npage; i++)
			copy_page(dev->data[page + i], buffer + PAGE_SIZE * i);

	} else {

		for (i = 0; i < npage; i++)
			copy_page(buffer + PAGE_SIZE * i, dev->data[page + i]);
		
	}
	

}

static void rmem_request(struct request_queue *q) 
{
	struct request *req;


	req = blk_fetch_request(q);
	while (req != NULL) {
		if (req == NULL || (req->cmd_type != REQ_TYPE_FS)) {
			printk (KERN_NOTICE "Skip non-CMD request\n");
			__blk_end_request_all(req, -EIO);
			continue;
		}
		rmem_transfer(devices[q->id], blk_rq_pos(req), blk_rq_cur_sectors(req),
				bio_data(req->bio), rq_data_dir(req));
		if ( ! __blk_end_request_cur(req, 0) ) {
			req = blk_fetch_request(q);
		}
	}
}

/*
 * The HDIO_GETGEO ioctl is handled in blkdev_ioctl(), which
 * calls this. We need to implement getgeo, since we can't
 * use tools such as fdisk to partition the drive otherwise.
 */
int rmem_getgeo(struct block_device * block_device, struct hd_geometry * geo) {
	long size;

	/* We have no real geometry, of course, so make something up. */
  //size = device.size * (PAGE_SIZE / KERNEL_SECTOR_SIZE);
  size = npages * PAGE_SIZE * (PAGE_SIZE / KERNEL_SECTOR_SIZE);
	geo->cylinders = (size & ~0x3f) >> 6;
	geo->heads = 4;
	geo->sectors = 16;
	geo->start = 0;
	return 0;
}

/*
 * The device operations structure.
 */
static struct block_device_operations rmem_ops = {
	.owner  = THIS_MODULE,
	.getgeo = rmem_getgeo
};



static int __init rmem_init(void) {
	int i,c,major_num;
  struct rmem_device* device;
  struct request_queue *queue;
  char dev_name[20];
  for(c = 0; c < DEVICE_BOUND; c++) {
    devices[c] = NULL;
  }
  for(c = 0; c < ndev; c++) {
  	device = vmalloc(sizeof(*device));
  	/*
  	 * Set up our internal device.
  	 */
  	device->size = npages * PAGE_SIZE;
  	spin_lock_init(&(device->lock));
  
  	device->data = vmalloc(npages * sizeof(u8 *));
  	if (device->data == NULL)
  		return -ENOMEM;
  
  	for (i = 0; i < npages; i++) {
  		device->data[i] = kmalloc(PAGE_SIZE, GFP_KERNEL);
  		if (device->data[i] == NULL) {
  			int j;
        pr_info("rmem: can not allocate data\n");
  			for (j = 0; j < i - 1; j++)
  				kfree(device->data[j]);
  			vfree(device->data);
  			return -ENOMEM;
  		}
  
  		memset(device->data[i], 0, PAGE_SIZE);
      if (i % 100000 == 0)
  			pr_info("rmem: allocated %dth page\n", i);
  	}
  
  	/*
  	 * Get a request queue.
  	 */
  	queue = blk_init_queue(rmem_request, &device->lock);
  	if (queue == NULL)
  		goto out;
    pr_info("init queue id %d\n", queue->id);
    if (queue->id >= DEVICE_BOUND) 
      goto out;
    devices[queue->id] = device;
    scnprintf(dev_name, 20, "rmem%d", queue->id);
  	blk_queue_physical_block_size(queue, PAGE_SIZE);
  	blk_queue_logical_block_size(queue, PAGE_SIZE);
  	blk_queue_io_min(queue, PAGE_SIZE);
  	blk_queue_io_opt(queue, PAGE_SIZE * 4);
  	/*
  	 * Get registered.
  	 */
  	major_num = register_blkdev(0, dev_name);
    device->major_num = major_num;
    pr_info("Registering blkdev %s major_num %d\n", dev_name, major_num);
    if (major_num < 0) {
  		printk(KERN_WARNING "rmem: unable to get major number\n");
  		goto out;
  	}
  	/*
  	 * And the gendisk structure.
  	 */
  	device->gd = alloc_disk(16);
  	if (!device->gd)
  		goto out_unregister;
  	device->gd->major = major_num;
  	device->gd->first_minor = 0;
  	device->gd->fops = &rmem_ops;
  	device->gd->private_data = device;
  	strcpy(device->gd->disk_name, dev_name);
  	set_capacity(device->gd, npages * SECTORS_PER_PAGE);
  	device->gd->queue = queue;
  	add_disk(device->gd);

  }
	return 0;

out_unregister:
	unregister_blkdev(major_num, dev_name);
out:
	for (i = 0; i < npages; i++)
		kfree(device->data[i]);
	vfree(device->data);
	return -ENOMEM;
}

static void __exit rmem_exit(void)
{
  int i,c;
  for(c = 0; c < DEVICE_BOUND; c++) {
    if(devices[c] != NULL){
    	del_gendisk(devices[c]->gd);
  	  put_disk(devices[c]->gd);
      pr_info("Unregistering blkdev %s major_num %d\n", devices[c]->gd->disk_name, devices[c]->major_num);
    	unregister_blkdev(devices[c]->major_num, devices[c]->gd->disk_name);
  	  blk_cleanup_queue(devices[c]->gd->queue);

  	  for (i = 0; i < npages; i++)
	    	kfree(devices[c]->data[i]);
  
    	vfree(devices[c]->data);
      vfree(devices[c]);
      devices[c] = NULL;
    }
  }

	pr_info("rmem: bye!\n");
}

module_init(rmem_init);
module_exit(rmem_exit);
