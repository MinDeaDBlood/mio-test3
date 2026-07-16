from __future__ import annotations

from src.core.image_size import image_logical_size


def dynamic_list_reader(path):
    """Read dynamic_partitions_op_list and return a group/partition mapping."""
    data = {}
    with open(path, 'r', encoding='utf-8') as l_f:
        for p in l_f.readlines():
            if p[:1] == '#':
                continue
            tmp = p.strip().split()
            if tmp[0] == 'remove_all_groups':
                data.clear()
            elif tmp[0] == 'add_group':
                data[tmp[1]] = {}
                data[tmp[1]]['size'] = tmp[2]
                data[tmp[1]]['parts'] = []
            elif tmp[0] == 'add':
                data[tmp[2]]['parts'].append(tmp[1])
    return data


def generate_dynamic_list(group_name: str, size: int, super_type: int, part_list: list, work):
    data = ['# Remove all existing dynamic partitions and groups before applying full OTA', 'remove_all_groups']
    with open(f"{work}/dynamic_partitions_op_list", 'w', encoding='utf-8', newline='\n') as d_list:
        if super_type == 1:
            data.append(f'# Add group {group_name} with maximum size {size}')
            data.append(f'add_group {group_name} {size}')
        elif super_type in [2, 3]:
            data.append(f'# Add group {group_name}_a with maximum size {size}')
            data.append(f'add_group {group_name}_a {size}')
            data.append(f'# Add group {group_name}_b with maximum size {size}')
            data.append(f'add_group {group_name}_b {size}')
        for part in part_list:
            if super_type == 1:
                data.append(f'# Add partition {part} to group {group_name}')
                data.append(f'add {part} {group_name}')
            elif super_type in [2, 3]:
                data.append(f'# Add partition {part}_a to group {group_name}_a')
                data.append(f'add {part}_a {group_name}_a')
                data.append(f'# Add partition {part}_b to group {group_name}_b')
                data.append(f'add {part}_b {group_name}_b')
        for part in part_list:
            if super_type == 1:
                part_size = image_logical_size(f"{work}/{part}.img")
                data.append(f'# Grow partition {part} from 0 to {part_size}')
                data.append(f'resize {part} {part_size}')
            elif super_type in [2, 3]:
                part_size = image_logical_size(f"{work}/{part}.img")
                data.append(f'# Grow partition {part}_a from 0 to {part_size}')
                data.append(f'resize {part}_a {part_size}')
        d_list.writelines([f"{key}\n" for key in data])
        data.clear()


__all__ = ['dynamic_list_reader', 'generate_dynamic_list']
