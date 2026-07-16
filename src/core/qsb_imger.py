"""
qsb {prefix}_*.img merger
v1.0
refer: https://ext4.wiki.kernel.org/index.php/Ext4_Disk_Layout#The_Super_Block
"""
from src.core.diagnostics import emit
import os.path
from struct import unpack
from xml.dom.minidom import parse


def process_by_xml(file: str, prefix='system', out_file_path: str = None):
    dom = parse(os.path.join(file))
    elems_program = dom.getElementsByTagName('program')
    basedir = os.path.dirname(file)
    count = len(elems_program)
    img_orders = []
    for i in range(count - 1):
        file_name = elems_program[i].getAttribute('filename')
        if file_name[0:len(prefix) + 1] == prefix + '_':
            n = int(file_name[file_name.find('_') + 1:file_name.find('.')])
            img_orders.append([n, i])

    if not len(img_orders):
        emit(f'No match: {prefix}')
        return False
    img_orders.sort()
    cur_pos_sector = 0
    base_sector = 0
    total_sectors = 0
    for img_order in img_orders:
        elem = elems_program[img_order[1]]
        file_name = elem.getAttribute('filename')
        file_sector_offset = int(elem.getAttribute('file_sector_offset'))
        start_sector = int(elem.getAttribute('start_sector'))
        num_partition_sectors = int(elem.getAttribute('num_partition_sectors'))
        if cur_pos_sector == 0:
            base_sector = start_sector
            SECTOR_SIZE_IN_BYTES = int(elem.getAttribute('SECTOR_SIZE_IN_BYTES'))
        emit(f'> {file_name}')
        emit('>> reading...')
        try:
            with open(os.path.join(basedir, file_name), 'rb') as in_file:
                in_data = in_file.read()
        except IOError:
            emit('<< failed!!!')
            return False

        if cur_pos_sector == 0:
            emit('>>> Analysing...')
            if in_data[1080] == 'S' and in_data[1081] == b'\xef':
                total_blocks = in_data[1028:1032]
                s_log_block_size = in_data[1048:1052]
                total_blocks, = unpack('i', total_blocks)
                s_log_block_size, = unpack('i', s_log_block_size)
                total_size = total_blocks * 1024 * pow(2, s_log_block_size)
                total_sectors = total_size / SECTOR_SIZE_IN_BYTES
                emit(f'<<< Total size(B): {total_size}')
            else:
                emit('<<< NOT ext4 img!!!')
            out_filename = os.path.join(basedir if out_file_path is None else out_file_path, f'{prefix}.img')
            out_file = open(out_filename, 'wb')
        fill_sectors = 0
        if 0 < cur_pos_sector < start_sector:
            fill_sectors = start_sector - cur_pos_sector
        fill_sectors += file_sector_offset
        if fill_sectors > 0:
            emit('<< filling...')
            out_file.write(fill_sectors * SECTOR_SIZE_IN_BYTES * b'\x00')
        emit('<< writing...')
        out_file.write(in_data)
        out_file.flush()
        cur_pos_sector = start_sector + num_partition_sectors

    fill_sectors = base_sector + total_sectors - cur_pos_sector
    if total_sectors > 0 and fill_sectors > 0:
        emit('<< extra filling...')
        out_file.write(fill_sectors * SECTOR_SIZE_IN_BYTES * b'\x00')
    out_file.close()
    emit(f'Finished: {out_filename}')
    return True


def _print_usage(app: str) -> None:
    emit('$: merge {prefix}_*.img\n@: 483E10D992F3776521A74B2F64AE2D37 (:\n#: 20161030 v1.0\n')
    emit(f'usage:\n{app} <rawprogram-xml-file> [img-prefix]')
    emit('    img-prefix: system (default), factory, cache, userdata ...')


def main(argv=None) -> int:
    import sys

    args = list(sys.argv[1:] if argv is None else argv)
    app = sys.argv[0]
    if not args:
        _print_usage(app)
        return 1

    source_file = args[0]
    prefix = args[1] if len(args) > 1 else 'system'
    if not os.path.isfile(source_file):
        emit(f'NO file: {source_file}')
        return 1

    return 0 if process_by_xml(source_file, prefix) else 1


if __name__ == '__main__':
    raise SystemExit(main())
