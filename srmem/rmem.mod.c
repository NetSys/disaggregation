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
	{ 0xffbbf9cb, __VMLINUX_SYMBOL_STR(module_layout) },
	{ 0xb6b46a7c, __VMLINUX_SYMBOL_STR(param_ops_int) },
	{ 0x9a9170c0, __VMLINUX_SYMBOL_STR(blk_cleanup_queue) },
	{ 0x2b78b0d, __VMLINUX_SYMBOL_STR(put_disk) },
	{ 0xd2011db7, __VMLINUX_SYMBOL_STR(del_gendisk) },
	{ 0x999e8297, __VMLINUX_SYMBOL_STR(vfree) },
	{ 0xb5a459dc, __VMLINUX_SYMBOL_STR(unregister_blkdev) },
	{ 0x65533ba8, __VMLINUX_SYMBOL_STR(add_disk) },
	{ 0xe914e41e, __VMLINUX_SYMBOL_STR(strcpy) },
	{ 0xe8452fa, __VMLINUX_SYMBOL_STR(alloc_disk) },
	{ 0x71a50dbc, __VMLINUX_SYMBOL_STR(register_blkdev) },
	{ 0x1f12041d, __VMLINUX_SYMBOL_STR(blk_queue_io_opt) },
	{ 0xc9da0bdb, __VMLINUX_SYMBOL_STR(blk_queue_io_min) },
	{ 0xd9452fd5, __VMLINUX_SYMBOL_STR(blk_queue_logical_block_size) },
	{ 0xd1e88137, __VMLINUX_SYMBOL_STR(blk_queue_physical_block_size) },
	{ 0x4ca9669f, __VMLINUX_SYMBOL_STR(scnprintf) },
	{ 0xfe8d9966, __VMLINUX_SYMBOL_STR(blk_init_queue) },
	{ 0x37a0cba, __VMLINUX_SYMBOL_STR(kfree) },
	{ 0xe6425630, __VMLINUX_SYMBOL_STR(kmem_cache_alloc_trace) },
	{ 0x8c74e643, __VMLINUX_SYMBOL_STR(kmalloc_caches) },
	{ 0xd6ee688f, __VMLINUX_SYMBOL_STR(vmalloc) },
	{ 0xcfbd216, __VMLINUX_SYMBOL_STR(__blk_end_request_all) },
	{ 0x27e1a049, __VMLINUX_SYMBOL_STR(printk) },
	{ 0x8d33d15e, __VMLINUX_SYMBOL_STR(__blk_end_request_cur) },
	{ 0x33b84f74, __VMLINUX_SYMBOL_STR(copy_page) },
	{ 0x8aa36262, __VMLINUX_SYMBOL_STR(blk_fetch_request) },
	{ 0xbdfb6dbb, __VMLINUX_SYMBOL_STR(__fentry__) },
};

static const char __module_depends[]
__used
__attribute__((section(".modinfo"))) =
"depends=";


MODULE_INFO(srcversion, "26F3888E6A15AA3DDEC23F6");
