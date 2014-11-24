#include <linux/module.h>
#include <linux/vermagic.h>
#include <linux/compiler.h>

MODULE_INFO(vermagic, VERMAGIC_STRING);

__visible struct module __this_module
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
	{ 0x59caa4c3, __VMLINUX_SYMBOL_STR(module_layout) },
	{ 0xb6b46a7c, __VMLINUX_SYMBOL_STR(param_ops_int) },
	{ 0x9725b589, __VMLINUX_SYMBOL_STR(proc_doulongvec_minmax) },
	{ 0x630034ef, __VMLINUX_SYMBOL_STR(single_release) },
	{ 0x79bc9e36, __VMLINUX_SYMBOL_STR(seq_read) },
	{ 0x9d05da80, __VMLINUX_SYMBOL_STR(seq_lseek) },
	{ 0xac3d20e2, __VMLINUX_SYMBOL_STR(unregister_sysctl_table) },
	{ 0x90586e31, __VMLINUX_SYMBOL_STR(blk_cleanup_queue) },
	{ 0xd26f8aee, __VMLINUX_SYMBOL_STR(put_disk) },
	{ 0xe40f8eaf, __VMLINUX_SYMBOL_STR(del_gendisk) },
	{ 0x999e8297, __VMLINUX_SYMBOL_STR(vfree) },
	{ 0xb5a459dc, __VMLINUX_SYMBOL_STR(unregister_blkdev) },
	{ 0x628121e9, __VMLINUX_SYMBOL_STR(register_sysctl_table) },
	{ 0xd31f2ab0, __VMLINUX_SYMBOL_STR(add_disk) },
	{ 0x3bb129dc, __VMLINUX_SYMBOL_STR(alloc_disk) },
	{ 0x71a50dbc, __VMLINUX_SYMBOL_STR(register_blkdev) },
	{ 0xd5441a9d, __VMLINUX_SYMBOL_STR(blk_queue_io_opt) },
	{ 0x5662372d, __VMLINUX_SYMBOL_STR(blk_queue_io_min) },
	{ 0x5bf29b8c, __VMLINUX_SYMBOL_STR(blk_queue_logical_block_size) },
	{ 0xe3a54fa5, __VMLINUX_SYMBOL_STR(blk_queue_physical_block_size) },
	{ 0xca73eadc, __VMLINUX_SYMBOL_STR(blk_init_queue) },
	{ 0x37a0cba, __VMLINUX_SYMBOL_STR(kfree) },
	{ 0x68565378, __VMLINUX_SYMBOL_STR(kmem_cache_alloc_trace) },
	{ 0xdab9e674, __VMLINUX_SYMBOL_STR(kmalloc_caches) },
	{ 0xd6ee688f, __VMLINUX_SYMBOL_STR(vmalloc) },
	{ 0xaed84047, __VMLINUX_SYMBOL_STR(proc_create_data) },
	{ 0xfa03f3e4, __VMLINUX_SYMBOL_STR(__blk_end_request_all) },
	{ 0x27e1a049, __VMLINUX_SYMBOL_STR(printk) },
	{ 0xcab3dd85, __VMLINUX_SYMBOL_STR(__blk_end_request_cur) },
	{ 0xda3e43d1, __VMLINUX_SYMBOL_STR(_raw_spin_unlock) },
	{ 0x3a26ed11, __VMLINUX_SYMBOL_STR(sched_clock) },
	{ 0x33b84f74, __VMLINUX_SYMBOL_STR(copy_page) },
	{ 0xd52bf1ce, __VMLINUX_SYMBOL_STR(_raw_spin_lock) },
	{ 0x4f68e5c9, __VMLINUX_SYMBOL_STR(do_gettimeofday) },
	{ 0xa8a9fcf8, __VMLINUX_SYMBOL_STR(blk_fetch_request) },
	{ 0xa05f372e, __VMLINUX_SYMBOL_STR(seq_printf) },
	{ 0x1742baec, __VMLINUX_SYMBOL_STR(single_open) },
	{ 0xbdfb6dbb, __VMLINUX_SYMBOL_STR(__fentry__) },
};

static const char __module_depends[]
__used
__attribute__((section(".modinfo"))) =
"depends=";


MODULE_INFO(srcversion, "5C9DC8E2931A93D58173350");
