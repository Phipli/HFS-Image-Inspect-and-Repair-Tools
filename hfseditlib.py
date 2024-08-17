#!/usr/bin/python3

# ######################################################### #
#            Classic Mac Disc Image Edit Library            #
# ######################################################### #
# Basic tool for fixing non-bootable classic mac disc images
# 5 February, 2024
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
# * Display Apple Partition Map details
# * View 512 byte pages
# * Allow user to edit Partition Map details
# * Select from a range of drivers
# * Set Boot Flags
# * Verify partition format
#	- Handle extracting partition from images with
#		multiple partitions
#	- Fix basic issues
# 	- Reject weird partitions

# Boot blocks are described in the Inside Macintosh "Files" publication.
#		Chapter "File Manager" section "Data Organization on Volumes"
# Partition Maps are described in the Inside Macintosh "Devices" publication
#		Chapter "SCSI Manager"
# Wikipedia is also handy.


## Library Imports ##

import sys
import os


## Debug Level ##

debugOn = 3 # 0 = silent, 1 = normal output, 2 = debug mode, 3 = verbose


## Constants and offsets ##

blockSize = 512 # each block (Apple) / sector (Wikipedia) is this many bytes
#					Additionally, a partition should be a multiple of this

# Partition Map
Apple_HFS_Type = "4170706c655f4846530000000000000000000000000000000000000000000000"
DiscFormatSig = "4552" # The signature at the very start of a disc
PartitionMapSig = "504d" # The signature at the start of a partition map block

prtMap_os = 512 # Offset to the first table/block/page in the partition map
# The following are offsets from the start of the current partition map block
prtSig_os = 0 # 2 bytes - Signature of each partition map block. Always "PM"
prtCount_os = 4 # 4 bytes - Total number of partitions
prtStart_os = 8 # 4 bytes - Start point of this partition in sectors
prtLength_os = 12 # 4 bytes - Length of this partition in sectors
prtName_os = 16 # 32 bytes String (left justified)
prtType_os = 48 # 32 bytes String (left justified)
prtDataStart_os = 80 # 4 bytes - Location of data on this partition
prtDataLength_os = 84 # 4 bytes - Length of data on this partition

# Boot Block
VolumeSig = "4c4b" # The signature at the start of a hfs volume (partition)

bootBlock_os = 0 # offset from start of volume in bytes or sectors
# the following are offsets from bootBlock
bbID_os = 0 # 2 bytes - partition ID - a volume is always 4C4B
bbEntry_os = 2 # 4 bytes - entry point to the boot code. Usually 6000
bbVersion_os = 6 # 2 bytes - "flag byte and boot block version number
bbPageFlags_os = 8 # 2 bytes - "Used Internally"
bbShellName_os = 26 # 16 bytes pascal string 15 chars - Usually 'Finder',
#			sometimes 'At Ease'. Default shell.
bbHelloName_os = 42 # 16 bytes pascal string 15 chars - Usually 'Finder.
#			This launches at boot.
# Master Directory Blocks
MasterDirBlock_os = 1024 # offset from start of volume in bytes
# the following are offsets from MasterDirBlock
drSigWord_os = 0 # 2 bytes - Describes what type of formatting the volume has.
#			HFS is 4244
drCrDate_os = 2 # 4 bytes - Volume creation date
drLsMod_os = 6 # 4 bytes - Volume last modification date
drNmAlBlks_os = 18 # 2 bytes - Total count of blocks
drFreeBlks_os = 34 # 2 bytes - Number of free blocks
drVN_os = 36 # 28 bytes pascal string 27 chars - Volume Name (as mounts on the desktop)
drFilCnt_os = 124 # 4 bytes - Number of files on volume.


## Functions ##

def dbugPrint(theText, dLevel):
	# A wrapper for some output text to set debug output level
	# 0 = silent, 1 = normal output, 2 = debug mode, 3 = verbose
	if(dLevel<=debugOn):
		print(theText)

def chkFileExists(theFile):
	dbugPrint("chkFileExists", 3)
	localStatus = False
	if(os.path.isfile(theFile)):
		localStatus = True
		dbugPrint("chkFile : The file " + theFile + " does exist.", 3)
	else:
		dbugPrint("Error : The File " + theFile + " was not found.", 2)
		dbugPrint("This error was generated in chkFile", 3)
	return localStatus

def partitionCount(theFile):
	dbugPrint("partitionCount", 3)
	partCount = -1
	i = prtMap_os
	if(chkFileExists(theFile)):
		fileLen = os.path.getsize(theFile)
		dbugPrint("partitionCount : The length of " + theFile + " is " + str(fileLen) + " bytes.", 3)
		f = open(theFile, "rb")
		try:
			f.seek(i+prtCount_os)
			mapDataCount = f.read(4).hex()
			dbugPrint("mapDataCount : " + mapDataCount, 3)
		except:
			dbugPrint("An error occured while counting partitions in " + theFile, 1)
		partCount = 0
		while i < fileLen:
			f.seek(i+prtSig_os)
			if(f.read(2).hex() == '504d'):
				# it is a partition map page
				partCount = partCount+1
				dbugPrint("Found " + str(partCount) + " partitions in the map so far.", 3)
				f.seek(i+prtCount_os)
				latestMapDataCount = f.read(4).hex()
				dbugPrint("latestMapDataCount : " + mapDataCount, 3)
				if(mapDataCount != latestMapDataCount):
					dbugPrint("The number of partitions recorded in the partition map of " + theFile + " is inconsistent.", 2)
					mapDataCount = -1 # mess up so it flaggs later
			else:
				# file is bad, or we've reached the end
				if(partCount==0):
					# bad file
					#partCount = 0
					dbugPrint("No partition map was found.", 2)
				if((mapDataCount != partCount.to_bytes(4, byteorder='big', signed=False).hex())):
					dbugPrint("There is a discrepancy in the number of partitions in " + theFile, 2)
					partCount = -1
				dbugPrint(str(partCount) + " partitions were found in the partition map.", 3)
				break
			i=i+blockSize
		f.close()
	return partCount

def partitionName(theFile, partNum):
	# partNum is of all types, and includes the partition map itself
	# the order is as they are in the table, not logically.
	# the first partition is partition 1
	dbugPrint("partitionName", 3)
	partName = ""
	localPartCount = partitionCount(theFile)
	if(localPartCount >= partNum):
		dbugPrint("We are looking for a partition within the correct number range.", 3)
		f = open(theFile, "rb")
		try:
			f.seek((partNum*blockSize)+prtName_os)
			partName = (str(f.read(32), encoding='utf-8')).rstrip('\x00')
			dbugPrint("We read in : " + partName, 3)
		except:
			partLength = -1
			dbugPrint("An error occured while reading the partition name of partition " + str(partNum) + " in " + theFile, 2)
		f.close()
	else:
		dbugPrint("Partition out of range", 2)
		dbugPrint("Can't access partition " + str(partNum) + " out of " + str(localPartCount) + " in " + theFile, 3)
	return partName

def partitionType(theFile, partNum):
	# partNum is of all types, and includes the partition map itself
	# the order is as they are in the table, not logically.
	# the first partition is partition 1
	dbugPrint("partitionType", 3)
	partType = ""
	localPartCount = partitionCount(theFile)
	if(localPartCount >= partNum):
		dbugPrint("We are looking for a partition within the correct number range.", 3)
		f = open(theFile, "rb")
		try:
			f.seek((partNum*blockSize)+prtType_os)
			partType = (str(f.read(32), encoding='utf-8')).rstrip('\x00')
			dbugPrint("We read in : " + partType, 3)
		except:
			partLength = -1
			dbugPrint("An error occured while reading the Type of the partition " + str(partNum) + " in " + theFile, 2)
		f.close()
	else:
		dbugPrint("Partition out of range", 2)
		dbugPrint("Can't access partition " + str(partNum) + " out of " + str(localPartCount) + " in " + theFile, 3)
	return partType

def partitionLength(theFile, partNum):
	# partNum is of all types, and includes the partition map itself
	# the order is as they are in the table, not logically.
	# the first partition is partition 1
	dbugPrint("partitionLength", 3)
	partLength = -1
	localPartCount = partitionCount(theFile)
	if(localPartCount >= partNum):
		dbugPrint("We are looking for a partition within the correct number range.", 3)
		f = open(theFile, "rb")
		if partNum == 0:
			tempRead = f.read(2)
			if tempRead == b'ER':
				# Start of a disk
				partLength = 1
		else:
			try:
				f.seek((partNum*blockSize)+prtLength_os)
				partLength = int.from_bytes(f.read(4), byteorder='big', signed=False)
				dbugPrint("We read in : " + str(partLength), 3)
			except:
				partLength = -1
				dbugPrint("An error occured while reading the partition length of partition " + str(partNum) + " in " + theFile, 2)
		f.close()
	else:
		dbugPrint("Partition out of range", 2)
		dbugPrint("Can't access partition " + str(partNum) + " out of " + str(localPartCount) + " in " + theFile, 3)
	return partLength

def partitionStart(theFile, partNum):
	# partNum is of all types, and includes the partition map itself
	# the order is as they are in the table, not logically.
	# the first partition is partition 1
	dbugPrint("partitionStart", 3)
	partStart = -1
	localPartCount = partitionCount(theFile)
	if(localPartCount >= partNum):
		dbugPrint("We are looking for a partition within the correct number range.", 3)
		f = open(theFile, "rb")
		if partNum == 0:
			tempRead = f.read(2)
			if tempRead == b'ER':
				# Start of a disk
				partStart = 0
		else:
			try:
				f.seek((partNum*blockSize)+prtStart_os)
				partStart = int.from_bytes(f.read(4), byteorder='big', signed=False)
				dbugPrint("We read in : " + str(partStart), 3)
			except:
				partStart = -1
				dbugPrint("An error occured while reading the start locaation of partition " + str(partNum) + " in " + theFile, 2)
		f.close()
	else:
		dbugPrint("Partition out of range", 2)
		dbugPrint("Can't access partition " + str(partNum) + " out of " + str(localPartCount) + " in " + theFile, 3)
	return partStart

def hfsPartitionCount(theFile):
	# count partitions with type "Apple_HFS" followed by 23 zeros.
	dbugPrint("hfsPartitionCount", 3)
	hfsPartCount = -1
	i = 0
	totalPartitionCount = partitionCount(theFile)
	if(totalPartitionCount > 0):
		f = open(theFile, "rb")
		hfsPartCount = 0
		try:
			for i in range(1, totalPartitionCount+1):
				f.seek((blockSize*i)+prtType_os)
				if(f.read(32).hex()==Apple_HFS_Type):
					hfsPartCount = hfsPartCount+1
		except:
			hfsPartCount = -1
			dbugPrint("An error occured while counting the number of HFS partitions in " + theFile, 2)
		f.close()
	else:
		dbugPrint("No partitions found at all.", 1)
	return hfsPartCount
	
def appendPartitions(inputFile, outputFile, startPartition, endPartition):
	# always append - code that is calling should delete unwanted existing files
	# Returns number of kBytes written
	status = 0
	currentPartition = startPartition
	## Verify Valid Files here ################
	fIn = open(inputFile, 'rb')
	fOut = open(outputFile, 'ab') ## apend
	while currentPartition <= endPartition:
		## get current partition start location
		pLocation = partitionStart(inputFile, currentPartition)
		pLength = partitionLength(inputFile, currentPartition)
		if pLocation == -1 or pLength == -1:
			dbugPrint("Error, partition not found.", 1)
			status = -1024
			break
		currentLocation = 0
		fIn.seek(pLocation*blockSize)
		while currentLocation < pLength:
			buff1 = fIn.read(512)
			fOut.write(buff1)
			currentLocation = currentLocation + 1
			status = status + 512
		currentPartition = currentPartition + 1
	fIn.close()
	fOut.close()
	return status/1024

def copyPartitionBlock(inputFile, outputFile, locationFrom, locationTo, fixOffset):
	## No error checking yet ##
	status = -1
	fIn = open(inputFile, 'rb')
	fOut = open(outputFile, 'r+b')
	fIn.seek(prtMap_os+(blockSize*(locationFrom-1)))
	buff1 = fIn.read(512)
	prevPartition = locationTo-1
	if prevPartition > 1:
		likelyLocation = partitionStart(outputFile, locationTo-1)+partitionLength(outputFile, locationTo-1)
	previousPartCount = partitionCount(outputFile)
	fOut.seek(prtMap_os+(blockSize*(locationTo-1)))
	fOut.write(buff1)
	if fixOffset:
		fOut.seek(prtMap_os+(blockSize*(locationTo-1)+prtStart_os))
		if prevPartition > 1:
			fOut.write((likelyLocation).to_bytes(4, byteorder='big', signed=False))
			#f.seek(prtMap_os+(blockSize*(locationTo-1)+prtData+prtDataStart_os))
			#f.write((fileSectorLength).to_bytes(4, byteorder='big', signed=False))
			status = 1
		elif prevPartition == 0:
			fOut.write((0).to_bytes(4, byteorder='big', signed=False))
			status = 2
		else:
			dbugPrint("Error!", 2)
	i = 1
	while i <= previousPartCount+1:
		fOut.seek(prtMap_os+(blockSize*(i-1)+prtCount_os))
		fOut.write((previousPartCount+1).to_bytes(4, byteorder='big', signed=False))
		print(i)
		i = i+1
	fOut.close()
	fIn.close()
	return status

def readProperty(theFile, theProperty):
	val1 = -1
	return val1

def writeProperty(theFile, theProperty):
	val1 = -1
	return val1

def verifyFile(theFile): ## add a check to see if it is a multiple of 512 bytes (int(os.path.getsize(theFile))==os.path.getsize(theFile))
	dbugPrint("verifyFile", 3)
	fileStatus = -1 # the default
	# does it exist?
	if(os.path.isfile(theFile)):
		dbugPrint("It is a file and it exists, which is good.", 3)
		fileStatus=1
		# so open the file
		f = open(theFile, "rb")
		try:
			firstTwoBytes = f.read(2).hex()
			dbugPrint("First two bytes are : " + firstTwoBytes, 3)
		except:
			dbugPrint("Error reading " + theFile + " to verify it.", 2)
			f.close()
			return -1
		# does it look like a partition?
		if(firstTwoBytes == "4c4b"):
			dbgPrint("It looks like a raw partition.", 3)
			fileStatus=fileStatus+2
		# does it look like a multi partition image?
		elif(firstTwoBytes == "4552"):
			dbgPrint("It seems to be a multi-partition disc image.", 3)
			fileStatus=fileStatus+4
		elif(firstTwoBytes == "0000"):
			# Let's make sure it isn't a partition missing the first two bytes
			nextFewBytes = f.read(14).hex()
			dbgPrint("The next few bytes are : " + nextFewBytes, 3)
			if(nextFewBytes == "6000008644180000065379737465"):
				# The rest of the first line matches a common form
				fileStatus=fileStatus+8
		# oh no! it isn't an image that we understand!
		else:
			dbgPrint("The file " + theFile + " is of a format that this program does not recognise, sorry.", 1)
			fileStatus=-1
		f.close()
	return fileStatus;

def verifyDrivers(theFile):
	dbugPrint("verifyDrivers", 3)
	fileStatus = -1 # the default
	# does it exist?
	if(os.path.isfile(theFile)):
		dbgPrint("The drivers file was found.", 3)
		if(partitionCount(theFile)>1):
			fileStatus=1
			# so open the file
			f = open(theFile, "rb")
			try:
				firstTwoBytes = f.read(2).hex()
				f.seek(blockSize)
				firstTwoBytesOfPartitionMap = f.read(2).hex()
				dbgPrint("First two bytes are : " + firstTwoBytes, 3)
				dbgPrint("The Partition table starts with : " + firstTwoBytesOfPartitionMap, 3)
			except:
				dbgPrint("Error reading drivers file.",2)
				f.close()
				exit()
			# does it look like the start of a disc?
			if((firstTwoBytes == DiscFormatSig) and (firstTwoBytesOfPartitionMap == PartitionMapSig)):
				dbgPrint("The Partition Map and Drivers seem to be formatted appropriately after a basic check.",3)
				fileStatus=fileStatus+2
			else:
				print("The drivers file is of a format that this program does not recognise.")
				#fileStatus=fieStatus+8
				fileStatus=-1
			f.close()
		else:
			dbgPrint("Couldn't verify the drivers file because it didn't contain an appropriate number of partitions in the partition map.", 3)
	return fileStatus;




