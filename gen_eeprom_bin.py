#******************************************************************************
# Copyright (c) 2023 Advanced Micro Devices, Inc. All Rights Reserved.
# SPDX-License-Identifier: MIT
#
# Description      : This script generates EEPROM bin Contents
# Author           : Sharathk
# Editor           : Gurgenbaby
# Version          : 1.0
#
#******************************************************************************
import os
import sys
import struct
import shutil
import datetime
import uuid
import binascii


bArray = bytearray()
sel = 0

def total_seconds(td):
    # Keep backward compatibility with Python 2.6 which doesn't have
    # this method
    if hasattr(td, 'total_seconds'):
        return td.total_seconds()
    else:
        return (td.microseconds + (td.seconds + td.days * 24 * 3600) * 10**6) / 10**6

def calc_uuid4(fp, pos):
    id = uuid.uuid4()
    data = id.hex
    for i in range(16):
        fp.seek(pos+i)
        fp.write(struct.pack("B", int(data[i*2:i*2+2], 16)))

def write_to_bin_file(fp, data, pos, size):
    fp.seek(pos)
    if len(data) > size:
        for i in range(size):
            fp.write(data[i])
    else:
        fp.write(data)

def calc_checksum(fp, num, pos):
    total_sum = 0
    fp.seek(pos)
    for i in range(num):
        total_sum = total_sum + int.from_bytes(fp.read(1), byteorder='big')
    lsb_byte = (total_sum & 0xFF) # mask the lower byte
    if lsb_byte == 0:
        return 0xFF
    else:
        # Using CheckSum8 2s Complement
        return (0x100 - lsb_byte)
    
def calc_mfg_time():
    current_time = datetime.datetime.now()
    diff_date = (current_time - datetime.datetime(1996, 1, 1))
    minutes = total_seconds(diff_date)/60
    #print(minutes)
    return minutes

#Menu selection for SOM/KV/KR/KD EEPROMS
sys.path.insert(1, './InputData/')
print("EEPROM binary generator\n")
print("Enter 1 for k26_som_eeprom")
print("Enter 2 for kv_cc_eeprom")
print("Enter 3 for kr_cc_eeprom")
print("Enter 4 for removing Output dir\n")

if not os.path.exists("Output"):
    os.makedirs("Output")

sel = int(input("Input: "))

if sel == 1:
    shutil.copyfile("./DataFeed/k26_som_ref.bin", "./Output/k26_som_eeprom.bin")
    filePtr = open("./Output/k26_som_eeprom.bin", "r+b")
    from k26_data import *
    print("K26 SOM EEPROM selected\n")
elif sel == 2:
    shutil.copyfile("./DataFeed/kv_cc_ref.bin", "./Output/kv_cc_eeprom.bin")
    filePtr = open("./Output/kv_cc_eeprom.bin", "r+b")
    from kv_cc_data import *
    print("KV CC SOM EEPROM selected\n")
elif sel == 3:
    shutil.copyfile("./DataFeed/kr_cc_ref.bin", "./Output/kr_cc_eeprom.bin")
    filePtr = open("./Output/kr_cc_eeprom.bin", "r+b")
    from kr_cc_data import *
    print("KR CC SOM EEPROM selected\n")
elif sel == 4:
    shutil.rmtree("Output")
    print("Output directory removed\n")
    exit()
else:
    print("Invalid Choice.")
    exit()

#Table: 4, SOM & CC Common Header and Board Area
#Common Header (8 Bytes)
print('Writing Common Header Area')
print('    | Size: 08 Bytes (0x00 - 0x07)')
write_to_bin_file(filePtr, bytes.fromhex(PRD_INFO_0x04), 0x4, 1)
write_to_bin_file(filePtr, struct.pack("B", calc_checksum(filePtr, 0x7, 0x0)), 0x7, 1)

#Board Info Area(96 or 72 Bytes)
print('\nWriting Board Info Area')
print('    | Size: 96 Bytes (0x08 - 0x67)')
bArray = struct.pack("<L", int(calc_mfg_time()))
write_to_bin_file(filePtr, bArray[:3], 0xB, 3)
write_to_bin_file(filePtr, bytes.fromhex(BRD_MANUFACTURER_0x0F), 0xF, 6)
if sel == 1:
    write_to_bin_file(filePtr, bytes.fromhex(BRD_PRODUCT_0x16), 0x16, 16)
write_to_bin_file(filePtr, bytes.fromhex(BRD_SERIAL_0x27), 0x27, 16)
write_to_bin_file(filePtr, bytes.fromhex(BRD_PART_0x38), 0x38, 9)
write_to_bin_file(filePtr, bytes.fromhex(REV_NUM_0x44), 0x44, 8)
write_to_bin_file(filePtr, bytes.fromhex(DEV_ID_0x4F), 0x4F, 2)
write_to_bin_file(filePtr, bytes.fromhex(SUB_VEN_ID_0x51), 0x51, 2)
write_to_bin_file(filePtr, bytes.fromhex(SUB_DEV_ID_0x53), 0x53, 2)
calc_uuid4(filePtr,0x56)
write_to_bin_file(filePtr, struct.pack("B", calc_checksum(filePtr, 0x5F, 0x8)),0x67, 1)

if sel == 1:
    #Table: 8, Xilinx SOM MAC Addr Multi Record
    print('Writing MAC Addr Multi Record Area...')
    write_to_bin_file(filePtr, SOM_MAC_ID_0_0x83.decode("hex"), 0x83, 6)
    write_to_bin_file(filePtr, struct.pack("B", calc_checksum(filePtr, 0xA, 0x7F)),0x7D, 1)
    write_to_bin_file(filePtr, struct.pack("B", calc_checksum(filePtr, 0x4, 0x7A)),0x7E, 1)

    #Table: 11, Xilinx SOM Memory Config Multi Record
    print('Writing Config Multi Record Area...')
    write_to_bin_file(filePtr, MEM_PRIMARY_0x99, 0x99, 12)
    write_to_bin_file(filePtr, MEM_SECONDARY_0xAE, 0xAE, 12)
    write_to_bin_file(filePtr, MEM_PS_DDR_0xC3, 0xC3, 12)
    write_to_bin_file(filePtr, MEM_PL_DDR_0xD8, 0xD8, 12)
    write_to_bin_file(filePtr, struct.pack("B", calc_checksum(filePtr, 0x57, 0x8E)),0x8C, 1)
    write_to_bin_file(filePtr, struct.pack("B", calc_checksum(filePtr, 0x4, 0x89)),0x8D, 1)
elif sel == 3:
    #Table: 9, Xilinx KR CC MAC Addr Multi Record
    print('Writing KR CC MAC Addr Multi Record Area...')
    write_to_bin_file(filePtr, KR_PS_MAC_ID_1_0x83.decode("hex"), 0x83, 6)
    write_to_bin_file(filePtr, KR_PL_MAC_ID_0_0x89.decode("hex"), 0x89, 6)
    write_to_bin_file(filePtr, KR_PL_MAC_ID_1_0x8F.decode("hex"), 0x8F, 6)
    write_to_bin_file(filePtr, struct.pack("B", calc_checksum(filePtr, 0x16, 0x7F)),0x7D, 1)
    write_to_bin_file(filePtr, struct.pack("B", calc_checksum(filePtr, 0x4, 0x7A)),0x7E, 1)
else:
    pass

print("EEPROM bin sucessfully generated")
filePtr.close()

