# ######################################################### #
#             Classic Mac Disc Image Inspector              #
# ######################################################### #
# Basic tool for viewing the pages of a HFS image in HEX.
# This is useful for inspecting the partition map and other
# things you might want to do when working with the format
# of classic Mac OS disk images.
#
# 1 February, 2024
# By Phipli
#
# Written for Python 3.10.12
#
# Version History
#
# 0.1 - Initial version. Previously called ViewPartitionMap.sh
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

if [[ -z $1 ]] ; then
	echo "Please indicate your target file containing an Apple Partition Map."
	echo "For example : ViewPartitionMap.sh ./MacOS8_1.iso"
	exit
fi

while [ true ]
do
	read -p "Select Apple Partition Map page [1, 2, 3... etc]  (q to quit): " thePage
	if [[ $thePage = "q" ]] ; then
		echo "Exiting..."
		exit
	fi
	if [[ ! $thePage =~ ^[0-9]+$ ]] ; then
		echo "Invalid entry"
		exit
	fi
	
	(( theOffset = thePage * 512 ))
	
	xxd -s $theOffset -l 512 "$1"
	echo ""
done
