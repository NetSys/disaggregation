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
	{ 0xe91ad96c, __VMLINUX_SYMBOL_STR(module_layout) },
	{ 0xdeffd09d, __VMLINUX_SYMBOL_STR(proc_doulongvec_minmax) },
	{ 0xba320a64, __VMLINUX_SYMBOL_STR(single_release) },
	{ 0xb4539def, __VMLINUX_SYMBOL_STR(seq_read) },
	{ 0x4b111755, __VMLINUX_SYMBOL_STR(seq_lseek) },
	{ 0xb6b46a7c, __VMLINUX_SYMBOL_STR(param_ops_int) },
	{ 0x9e2de6b, __VMLINUX_SYMBOL_STR(unregister_sysctl_table) },
	{ 0xd7a3cf11, __VMLINUX_SYMBOL_STR(blk_cleanup_queue) },
	{ 0x2cb9eac2, __VMLINUX_SYMBOL_STR(put_disk) },
	{ 0xfc0f7c78, __VMLINUX_SYMBOL_STR(del_gendisk) },
	{ 0x999e8297, __VMLINUX_SYMBOL_STR(vfree) },
	{ 0xb5a459dc, __VMLINUX_SYMBOL_STR(unregister_blkdev) },
	{ 0xb68b7816, __VMLINUX_SYMBOL_STR(register_sysctl_table) },
	{ 0x4b5d5a67, __VMLINUX_SYMBOL_STR(add_disk) },
	{ 0x5369e608, __VMLINUX_SYMBOL_STR(alloc_disk) },
	{ 0x71a50dbc, __VMLINUX_SYMBOL_STR(register_blkdev) },
	{ 0x2b1cb0d0, __VMLINUX_SYMBOL_STR(blk_queue_io_opt) },
	{ 0xfdd4bf16, __VMLINUX_SYMBOL_STR(blk_queue_io_min) },
	{ 0x6b1dc54d, __VMLINUX_SYMBOL_STR(blk_queue_logical_block_size) },
	{ 0xe5e635fa, __VMLINUX_SYMBOL_STR(blk_queue_physical_block_size) },
	{ 0x32e41e6a, __VMLINUX_SYMBOL_STR(blk_init_queue) },
	{ 0x37a0cba, __VMLINUX_SYMBOL_STR(kfree) },
	{ 0x3928c21e, __VMLINUX_SYMBOL_STR(kmem_cache_alloc_trace) },
	{ 0x7325f865, __VMLINUX_SYMBOL_STR(kmalloc_caches) },
	{ 0xd6ee688f, __VMLINUX_SYMBOL_STR(vmalloc) },
	{ 0x99def23a, __VMLINUX_SYMBOL_STR(proc_create_data) },
	{ 0xb5be5cc3, __VMLINUX_SYMBOL_STR(__blk_end_request_all) },
	{ 0x27e1a049, __VMLINUX_SYMBOL_STR(printk) },
	{ 0x4f68e5c9, __VMLINUX_SYMBOL_STR(do_gettimeofday) },
	{ 0x34765f8b, __VMLINUX_SYMBOL_STR(__blk_end_request_cur) },
	{ 0x3a26ed11, __VMLINUX_SYMBOL_STR(sched_clock) },
	{ 0x33b84f74, __VMLINUX_SYMBOL_STR(copy_page) },
	{ 0xcc75c3ea, __VMLINUX_SYMBOL_STR(blk_fetch_request) },
	{ 0x68e2f221, __VMLINUX_SYMBOL_STR(_raw_spin_unlock) },
	{ 0x103ecc35, __VMLINUX_SYMBOL_STR(seq_printf) },
	{ 0x67f7403e, __VMLINUX_SYMBOL_STR(_raw_spin_lock) },
	{ 0xf3b980c, __VMLINUX_SYMBOL_STR(single_open) },
	{ 0xbdfb6dbb, __VMLINUX_SYMBOL_STR(__fentry__) },
};

static const char __module_depends[]
__used
__attribute__((section(".modinfo"))) =
"depends=";


MODULE_INFO(srcversion, "FD52A8A02C7D0C2090E6F94");
