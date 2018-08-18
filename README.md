# super-beheader

Remove copier headers from SNES roms (aka SMC to SFC converter).

## What

SNES game dumps use the extension `.sfc`, for Super Famicom. But many roms use the extension `.smc` instead. What's the difference between these two file types?

`SMC` stands for Super Magicom, a game backup device that would add an extra header to the dumped ROM.

`SMC` files are basically `SFC` files with an extra set of bits prepended to the game ROM.

## Why

Most SNES emulators can run both `SFC` and `SMC` files, just ignoring the extra headers.

Some patches, though, expect the "raw" `SFC` file to apply cleanly.

Some emulator frontends, like [OpenEmu](https://openemu.org/), require the `SFC` file to calculate a hash that will be used to retrieve game metadata (like cover image) from online databases.

Being able to convert from `SMC` to `SFC` can prove useful in these cases and probably others.

## How

```
$ super-beheader.py -h
usage: super-beheader.py [-h] [-o OUTPUT_DIR] [-z] inputs [inputs ...]

Remove copier headers from SNES roms (aka SMC -> SFC).

positional arguments:
  inputs                roms to behead

optional arguments:
  -h, --help            show this help message and exit
  -o OUTPUT_DIR, --output-dir OUTPUT_DIR
                        output directory
  -z, --zipped          zip resulting SFC
```
