#!/usr/bin/python3

# ######################################################### #
#           Classic Mac Disc Image Partition List           #
# ######################################################### #
# Basic tool for fixing non-bootable classic mac disc images
# 1 February, 2024
# By Phipli
#
# Written for Python 3.10.12
#
# Version History
#
# 0.2 - Initial version. Transfered from Driver Fix Script.
#		The version number has been maintained for
#		continuity.
#		
#		
#
# Feature Requests
#
# * none
# *

# Boot blocks are described in the Inside Macintosh "Files" publication.
#		Chapter "File Manager" section "Data Organization on Volumes"
# Partition Maps are described in the Inside Macintosh "Devices" publication
#		Chapter "SCSI Manager"
# Wikipedia is also handy.


## Library Imports ##

import sys
import hfseditlib as hfs

hfs.debugOn = 1

## MAIN

# Verify arguments
# print(len(sys.argv))
if(len(sys.argv) == 2):
	print("The target disc image file is... " + sys.argv[1])
	inputFilePath = sys.argv[1]
else:
	print("Command format : " + sys.argv[0] + " <image_file_name.iso>")
	exit()

tableData = [["Num.", "Name", "Type", "Start", "Size"]]

numPartitions = hfs.partitionCount(inputFilePath)
if(numPartitions < 1):
	print("File doesn't appear to contain any partitions.")
	exit()

for i in range(1, numPartitions+1):
	tableData.append([str(i), hfs.partitionName(inputFilePath, i), hfs.partitionType(inputFilePath, i), hfs.partitionStart(inputFilePath, i), hfs.partitionLength(inputFilePath, i)])

for row in tableData:
	print("{: >5} {: >24} {: >24} {: >8} {: >8}".format(*row))


