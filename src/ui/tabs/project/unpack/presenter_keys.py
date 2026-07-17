from __future__ import annotations

METADATA_PATH = "project_unpack_metadata_path"
METADATA_TYPE = "project_unpack_metadata_type"
METADATA_SIZE = "project_unpack_metadata_size"

EXT4_MAGIC_NUMBER = "project_unpack_metadata_ext4_magic_number"
EXT4_VOLUME_NAME = "project_unpack_metadata_ext4_volume_name"
EXT4_UUID = "project_unpack_metadata_ext4_uuid"
EXT4_LAST_MOUNTED_ON = "project_unpack_metadata_ext4_last_mounted_on"
EXT4_BLOCK_SIZE = "project_unpack_metadata_ext4_block_size"
EXT4_BLOCK_COUNT = "project_unpack_metadata_ext4_block_count"
EXT4_FREE_INODES = "project_unpack_metadata_ext4_free_inodes"
EXT4_FREE_BLOCKS = "project_unpack_metadata_ext4_free_blocks"
EXT4_INODES_PER_GROUP = "project_unpack_metadata_ext4_inodes_per_group"
EXT4_BLOCKS_PER_GROUP = "project_unpack_metadata_ext4_blocks_per_group"
EXT4_INODE_COUNT = "project_unpack_metadata_ext4_inode_count"
EXT4_RESERVED_GDT_BLOCKS = "project_unpack_metadata_ext4_reserved_gdt_blocks"
EXT4_INODE_SIZE = "project_unpack_metadata_ext4_inode_size"
EXT4_FILESYSTEM_CREATED = "project_unpack_metadata_ext4_filesystem_created"
EXT4_CURRENT_SIZE = "project_unpack_metadata_ext4_current_size"

__all__ = [name for name in globals() if name.isupper()]
