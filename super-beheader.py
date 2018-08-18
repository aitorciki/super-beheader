#!/usr/bin/env python3

import argparse
import glob
import logging, logging.handlers
import multiprocessing
import os
import shutil
import sys
import tempfile
import zipfile


def existing_dir(path):
    try:
        os.makedirs(path, exist_ok=True)
    except Exception as e:
        raise argparse.ArgumentTypeError(e)

    return path

def get_logger():
    return logging.getLogger(str(os.getpid()))

def setup_logging():
    root_logger = logging.getLogger(__name__)
    root_logger.addHandler(logging.StreamHandler())

    # Setup a logger that buffers messages per process.
    # The buffer will be flushed at the end of every rom processing
    # to ensure all records are sorted properly.
    buffer = logging.handlers.MemoryHandler(1024, flushLevel=100, target=root_logger)
    logger = get_logger()
    logger.addHandler(buffer)
    logger.setLevel(logging.INFO)

def init_pool(_lock):
    global lock
    lock = _lock

    setup_logging()

def unzip_roms(rom, output_dir):
    extracted = []
    path = os.path.join(output_dir, os.path.splitext(rom)[0])

    with zipfile.ZipFile(rom) as zrom:
        members = [
            m for m in zrom.namelist()
            if os.path.splitext(m)[1].lower() in ('.smc', '.sfc')
        ]
        zrom.extractall(path, members)
        extracted = glob.glob(f'{path}/**/*.s[mf]c', recursive=True)

    return extracted

def zip_rom(rom, output_file):
    with zipfile.ZipFile(output_file, 'w', zipfile.ZIP_DEFLATED) as zrom:
        zrom.write(rom, os.path.basename(rom))

def safe_output(output):
    if not os.path.exists(output):
        return output

    name, ext = os.path.splitext(output)
    suffix = 0

    while True:
        output = f'{name}.beheaded{"." + str(suffix) if suffix else ""}{ext}'
        suffix = suffix + 1

        if not os.path.exists(output):
            break

    return output

def behead(rom, output_dir):
    logger = get_logger()

    name, _ = os.path.splitext(os.path.basename(rom))
    output = safe_output(os.path.join(output_dir, f'{name}.sfc'))

    cheader_size = os.path.getsize(rom) % 1024

    logger.info(f'Rom: {name} - {"SMC" if cheader_size else "SFC"} format')

    with open(rom, 'rb') as fin:
        with open(output, 'wb') as fout:
            fout.write(fin.read()[cheader_size:])

    return output

def process(input_, output_dir, tmp_dir, zipped):
    logger = get_logger()

    roms = [input_]

    if zipfile.is_zipfile(input_):
        roms = unzip_roms(input_, tmp_dir)

    for rom in roms:
        sfc = behead(rom, tmp_dir)
        basename = os.path.basename(sfc)

        if zipped:
            name, _ = os.path.splitext(basename)
            output = safe_output(os.path.join(output_dir, f'{name}.zip'))
            zip_rom(sfc, output)

        else:
            output = safe_output(os.path.join(output_dir, basename))
            shutil.copy(sfc, output)

        logger.info(f'Beheaded SFC available in {output}')

def main(*args):
    logger = get_logger()

    try:
        process(*args)
    except Exception as e:
        logger.error(e)
    finally:
        logger.info('--')

        # flush the memory handler to the shared logger, locking other
        # processes from flushing concurrently to ensure record ordering
        lock.acquire()
        logger.handlers[0].flush()
        lock.release()


if __name__ == '__main__':
    p = argparse.ArgumentParser(
        description='Remove copier headers from SNES roms (aka SMC -> SFC)'
    )
    p.add_argument('inputs', nargs='+', help='roms to behead')
    p.add_argument('-o', '--output-dir', default='.', type=existing_dir, help='output directory')
    p.add_argument('-z', '--zipped', action='store_true', help='zip resulting SFC')
    args = p.parse_args()

    lock = multiprocessing.Lock()

    with tempfile.TemporaryDirectory() as tmp_dir:
        items = [(f, args.output_dir, tmp_dir, args.zipped) for f in args.inputs]

        with multiprocessing.Pool(initializer=init_pool, initargs=(lock,)) as pool:
            pool.starmap(main, items)
