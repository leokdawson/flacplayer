""" FLAC metadata parser"""
# figure out endianness issues, why does it seem to work?
# flac encodes big endian, intel uses little endian, yet no issues...?
# is endianness just how it is stored maybe?
import sys
import os
import binascii

# note: from python3.7+ dicts are insertion ordered as language feature
streaminfo_block_bitsizes = {
    "flac": 32,
    "last_block": 1,
    "block_type": 7,
    "mdata_bytelen": 24,
    "minblocksize": 16,
    "maxblocksize": 16,
    "minframesize": 24,
    "maxframesize": 24,
    "samplerate": 20,
    "numchannels": 3,
    "bitspersample": 5,
    "totalsamples": 36,
    "md5hash": 128,
}
blocktype = {
    0: "STREAMINFO",
    1: "PADDING",
    2: "APPLICATION",
    3: "SEEKTABLE",
    4: "VORBIS_COMMENT",
    5: "CUESHEET",
    6: "PICTURE",
    127: "INVALID",
}
input_file_streaminfo = os.path.expanduser("~/Desktop/forshovelry.flac")
streaminfo_size = 0
for k, v in streaminfo_block_bitsizes.items():
    streaminfo_size += v
streaminfo_bytesize = streaminfo_size // 8
print(streaminfo_bytesize)

with open(input_file_streaminfo, "rb") as f:
    # maybe just read as ascii then convert to int?
    streaminfo_bytes = binascii.hexlify(f.read(streaminfo_bytesize))

streaminfo_ints = [
    int(streaminfo_bytes[i : i + 2], 16)  # endian decision point?
    for i in range(len(streaminfo_bytes))
    if i % 2 == 0
]

streaminfo_bits = [bin(x)[2:].zfill(8) for x in streaminfo_ints]
streaminfo_bits_1string = "".join(streaminfo_bits)

# print(streaminfo_bytes)
# print(streaminfo_ints)
# print(streaminfo_bits)
# print(streaminfo_bits_1string)

streaminfo_parsed_bits = []
streaminfo_pos_counter = 0
for k, v in streaminfo_block_bitsizes.items():
    streaminfo_parsed_bits.append(
        streaminfo_bits_1string[streaminfo_pos_counter : streaminfo_pos_counter + v]
    )
    streaminfo_pos_counter += v

print(streaminfo_parsed_bits)
error_check = streaminfo_bits_1string == "".join(streaminfo_parsed_bits)
print(error_check)


init_string = "".join(
    [
        chr(int(x, 2))
        for x in [
            streaminfo_parsed_bits[0][i : i + 8]
            for i in range(0, len(streaminfo_parsed_bits[0]), 8)
        ]
    ]
)
print(f"This file is encoded with {init_string}")

last_block = bool(int(streaminfo_parsed_bits[1]))
print(f"Last block: {last_block}")

blocktype_key = int(streaminfo_parsed_bits[2], 2)
print(f"Block type: {blocktype[blocktype_key]}")

metadata_length = int(streaminfo_parsed_bits[3], 2)
print(
    f"This metadata block is of size {metadata_length} bytes | {metadata_length*8} bits"
)

min_stream_blocksize = int(streaminfo_parsed_bits[4], 2)
print(f"Minimum stream blocksize (in samples): {min_stream_blocksize}")

max_stream_blocksize = int(streaminfo_parsed_bits[5], 2)
print(f"Maximum stream blocksize (in samples) {max_stream_blocksize}")

min_stream_framesize = int(streaminfo_parsed_bits[6], 2)
print(f"Minimum stream framesize (in bytes): {min_stream_framesize}")

max_stream_framesize = int(streaminfo_parsed_bits[7], 2)
print(f"Maximum stream framesize (in bytes): {max_stream_framesize}")

sample_rate = int(streaminfo_parsed_bits[8], 2)
print(f"Sample rate (in Hz.): {sample_rate}")

num_channels = int(streaminfo_parsed_bits[9], 2)
num_channels = num_channels + 1  # as per flac spec.
print(f"Number of channels: {num_channels}")

bits_per_sample = int(streaminfo_parsed_bits[10], 2)
bits_per_sample = bits_per_sample + 1  # as per flac spec.
print(f"Bits per. sample: {bits_per_sample}")

total_stream_samples = int(streaminfo_parsed_bits[11], 2)
if total_stream_samples == 0:
    print(f"Total number of samples in stream: UNKNOWN")
else:
    print(f"Total number of samples in stream: {total_stream_samples}")

md5_hash = hex(int(streaminfo_parsed_bits[12], 2))[2:]
print(f"The MD5 hash of the unencoded audio data: {md5_hash}")

# section dealing with reading in unspecified number of metadata blocks
# should be able to join with above section into one method eventually
# should I convert all to bits at start?
# or try and do it as we reach each block...?
print("\n" * 2)
input_file = os.path.expanduser("~/Desktop/forshovelry.flac")
with open(input_file, "rb") as f:
    # full_input_data = binascii.hexlify(f.read())
    full_input_data = f.read()  # try as simple read ascii for now

# print(len(full_input_data))
# testint2 = int(full_input_data[0])
# print(testint2)
# bintest = bin(testint2)[2:].zfill(8)
# print(bintest)

# # below, access section of bytes elements, prints as ascii
# # access an individual elements directly, prints as number...?
# print(full_input_data[7:8], type(full_input_data[7:8]))
# print(full_input_data[7], type(full_input_data[7]))
# # because of the above, the int conversion step could be redundant...
# # but safe to do it for now anyway

# metadata_header_sizes = {"lastmetablock": 1, "blocktype": 7, "blocklength": 24}
# metadata_header_length = 0
# for k, v in metadata_header_sizes.items():
#     metadata_header_length += v
# metadata_header_length = metadata_header_length // 8

# file_byte_location = 4
# current_block = full_input_data[
#     file_byte_location : file_byte_location + metadata_header_length
# ]
# file_byte_location += metadata_header_length

# print(current_block)
# current_block_ints = [int(x) for x in current_block]
# print(current_block_ints)
# current_block_bits = [bin(x)[2:].zfill(8) for x in current_block_ints]
# print(current_block_bits)
# current_block_bitstring = "".join(current_block_bits)
# print(current_block_bitstring)
# current_block_parsed = []
# current_block_pos = 0
# for k, v in metadata_header_sizes.items():
#     current_block_parsed.append(
#         current_block_bitstring[current_block_pos : current_block_pos + v]
#     )
#     current_block_pos += v
# print(current_block_parsed)
# current_block_length = int(current_block_parsed[2], 2)
# print(current_block_length)
# file_byte_location += current_block_length


def metablock_seeker(
    input_data, current_file_location, metaheader_size=4, metaheader_subsize=(1, 7, 24)
):
    """Seek through all metadata blocks in input data"""
    current_block = input_data[
        current_file_location : current_file_location + metaheader_size
    ]
    current_bits = [bin(x)[2:].zfill(8) for x in current_block]
    current_1string = "".join(current_bits)
    current_parsed = []
    string_pos = 0
    for v in metaheader_subsize:
        current_parsed.append(current_1string[string_pos : string_pos + v])
        string_pos += v
    print(
        f"This metablock is of type: {int(current_parsed[1], 2)}",
        f"  {current_parsed[0]}",
    )
    current_file_location += int(current_parsed[2], 2) + metaheader_size
    print(current_file_location)
    if current_parsed[0] == "1":
        print("You have reached the last metablock")
        current_file_location = -1
    return current_file_location


current_location = 4
while current_location != -1:
    current_location = metablock_seeker(full_input_data, current_location)

