# HFS Image Inspect and Repair Tools
This repository contains some small Python tools I made when I was inspecting and modifying classic Mac OS CD images.

<b>listPartitions.py</b>

This script inspects the provided disk image and provides basic details from the partition table. This requires hfseditlib.py

<b>ViewHFSPages.sh</b>

Basically a Hex viewer that uses pages matching the size of pages in the partition table of a HFS disk. This makes it fairly easy to navigate and inspect the partition table and boot blocks of a hard disk image.

<b>hfseditlib.py</b>

A slightly complicated mess of functions useful for manipulating and repairing HFS disk images. Using these functions you can assemble a new image from a collection of parts, a driver from one location, multiple partitions from others, and update the partition map for the new arrangement.

<b>driverModified</b>

An example bootable CD driver - in fact this is the partition table and drivers. Usefull for placing before raw partition images when someone has only imaged the data partition and you want to make the disk image bootable, but be warned, you need to make sure that the partition table is updated for the partitions you are using it with.

Sorry that there isn't more information here on how to use these scripts, but I wrote them several months ago.

My own saved notes are available in notes.txt.
