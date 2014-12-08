#include <linux/module.h>
#include <linux/vermagic.h>
#include <linux/compiler.h>

MODULE_INFO(vermagic, VERMAGIC_STRING);

struct module __this_module
__attribute__((section(".gnu.linkonce.this_module"))) = {
	.name = KBUILD_MODNAME,
	.init = init_module,
#ifdef CONFIG_MODULE_UNLOAD
	.exit = cleanup_module,
#endif
	.arch = MODULE_ARCH_INIT,
};

static const struct modversion_info ____versions[]
__used
__attribute__((section("__versions"))) = {
	{ 0x9a31bb74, "module_layout" },
	{ 0x9725b589, "proc_doulongvec_minmax" },
	{ 0xf192d0b1, "single_release" },
	{ 0xca67c6cb, "seq_read" },
	{ 0xd764127b, "seq_lseek" },
	{ 0x15692c87, "param_ops_int" },
	{ 0xac3d20e2, "unregister_sysctl_table" },
	{ 0xd22b0d61, "blk_cleanup_queue" },
	{ 0x60f77be2, "put_disk" },
	{ 0xc2e7f487, "del_gendisk" },
	{ 0x999e8297, "vfree" },
	{ 0xb5a459dc, "unregister_blkdev" },
	{ 0x628121e9, "register_sysctl_table" },
	{ 0xb8903622, "add_disk" },
	{ 0x64fff4b5, "alloc_disk" },
	{ 0x71a50dbc, "register_blkdev" },
	{ 0x9d95731e, "blk_queue_io_opt" },
	{ 0x80bf60bd, "blk_queue_io_min" },
	{ 0xd41957e6, "blk_queue_logical_block_size" },
	{ 0xaa6266d5, "blk_queue_physical_block_size" },
	{ 0x5f22f4ee, "blk_init_queue" },
	{ 0x37a0cba, "kfree" },
	{ 0xd61adcbd, "kmem_cache_alloc_trace" },
	{ 0x5cd9dbb5, "kmalloc_caches" },
	{ 0xd6ee688f, "vmalloc" },
	{ 0x26034a58, "proc_create_data" },
	{ 0x89413870, "__blk_end_request_all" },
	{ 0x27e1a049, "printk" },
	{ 0x4f68e5c9, "do_gettimeofday" },
	{ 0x8291af29, "__blk_end_request_cur" },
	{ 0x3a26ed11, "sched_clock" },
	{ 0x33b84f74, "copy_page" },
	{ 0x92c7baec, "blk_fetch_request" },
	{ 0xadaabe1b, "pv_lock_ops" },
	{ 0x789bdca3, "seq_printf" },
	{ 0xd52bf1ce, "_raw_spin_lock" },
	{ 0xbf50d31, "single_open" },
	{ 0xbdfb6dbb, "__fentry__" },
};

static const char __module_depends[]
__used
__attribute__((section(".modinfo"))) =
"depends=";


MODULE_INFO(srcversion, "FD52A8A02C7D0C2090E6F94");
