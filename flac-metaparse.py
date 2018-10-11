"""Functions to parse and print metadata of fLaC file"""
import os
import binascii
from PIL import Image

metaheader_block_format = {"last_block": 1, "block_type": 7, "mdata_bytelen": 24}
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
streaminfo_block_format = {
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
seekpoint_block_format = {"samplenumber": 64, "offset": 64, "numsamples": 16}
vorbis_block_format = {}
picture_block_format = {}


def read_file(filepath):
    """reads full flac file from specified path, converts to list of bin 
       strings
       """
    with open(os.path.expanduser(filepath), "rb") as f:
        full_file_data = f.read()
    full_file_data_bin = [bin(x)[2:].zfill(8) for x in full_file_data]
    return full_file_data_bin


def confirm_flac(file_data):
    """reads first 4 bytes of file, checks if it contains 'fLaC'"""
    flac_string = "".join([chr(int(x, 2)) for x in file_data[:4]])
    if flac_string == "fLaC":
        return flac_string
    print("File is not of type: fLaC or is incorrectly encoded")
    return False


def meta_streamparser(metablock_data):
    # """deals with parsing streaminfo data"""
    print("in STREAMINFO block")
    expected_size = 0
    for k, v in streaminfo_block_format.items():
        expected_size += v
    expected_size = expected_size // 8
    actual_size = len(metablock_data)
    if actual_size != expected_size:
        print(f"STREAMINFO: expected {expected_size} bytes, receieved {actual_size}")
        return -1
    streaminfo_format = []
    for k, v in streaminfo_block_format.items():
        streaminfo_format.append(v)
    streaminfo_format = tuple(streaminfo_format)
    streaminfo_1string = "".join(byte for byte in metablock_data)
    parsed_streaminfo = []
    string_pos = 0
    for section in streaminfo_format:
        parsed_streaminfo.append(streaminfo_1string[string_pos : string_pos + section])
        string_pos += section
    # print(parsed_streaminfo)
    parsed_streaminfo = {
        "minblocksize": int(parsed_streaminfo[0], 2),
        "maxblocksize": int(parsed_streaminfo[1], 2),
        "minframesize": int(parsed_streaminfo[2], 2),
        "maxframesize": int(parsed_streaminfo[3], 2),
        "samplerate": int(parsed_streaminfo[4], 2),
        "numchannels": int(parsed_streaminfo[5], 2) + 1,
        "bitspersample": int(parsed_streaminfo[6], 2) + 1,
        "totalsamples": int(parsed_streaminfo[7], 2),
        "md5hash": int(parsed_streaminfo[8], 2),
    }
    return parsed_streaminfo


def meta_seekparser(metablock_data):
    """deals with parsing seektable data, for now super basic minimum
       I don't full understand the seektable/seekpoint concept yet
       I think I need to work with a file with >1 seekpoint to learn how
       to work with it, seekpoints seem related to file length in terms of
       when they are used at least
       Perhaps to make seeking more efficient as file size gets larger, with
       more audio frames...
       """
    # print("in SEEKTABLE block")
    num_seekpoints = len(metablock_data) // 18
    first_sample_number = int("".join([x for x in metablock_data[:8]]), 2)
    byte_offset = int("".join([x for x in metablock_data[8:16]]), 2)
    num_samples = int("".join([x for x in metablock_data[16:18]]), 2)
    parsed_seekpoints = {
        "firstsample": first_sample_number,
        "byteoffset": byte_offset,
        "numsamples": num_samples,
    }
    if num_seekpoints > 1:
        print(f"WARNING: there are {num_seekpoints} seekpoints in this fLaC file")
    return parsed_seekpoints


def meta_vorbisparser(metablock_data):
    """deals with parsing vorbis_comment data
       notice the quirk here when trying to reverse slice for little endian ints
       it means the update blockpos has not been used yet, which leads to the -1
       in the next little-endian int reading
       LEARN AND USE STRUCT MODULE, DESIGNED TO DEAL WITH THIS STUFF
       """
    # print("in VORBIS_COMMENT block")
    blockpos = 0
    vendorlen = int("".join(metablock_data[3::-1]), 2)  # little-end NB: slice direction
    blockpos += 4
    vendorstr = "".join(
        [chr(int(x, 2)) for x in metablock_data[blockpos : vendorlen + blockpos]]
    )
    blockpos += vendorlen
    commentlistlen = int("".join(metablock_data[blockpos + 3 : blockpos - 1 : -1]), 2)
    blockpos += 4
    parsed_vorbis = {
        "vendorlength": vendorlen,
        "vendorstring": vendorstr,
        "comment_list_length": commentlistlen,
    }
    itercontrol = 0
    while itercontrol < commentlistlen:
        commentlen = int("".join(metablock_data[blockpos + 3 : blockpos - 1 : -1]), 2)
        blockpos += 4
        itercomment = "".join(
            [chr(int(x, 2)) for x in metablock_data[blockpos : blockpos + commentlen]]
        )
        blockpos += commentlen
        equal_sign_index = itercomment.index("=")
        comment_name = itercomment[:equal_sign_index]
        itercomment = itercomment[equal_sign_index + 1 :]
        parsed_vorbis[comment_name] = itercomment
        itercontrol += 1
    return parsed_vorbis


def meta_pictureparser(metablock_data):
    """deals with parsing picture data"""
    # print("in PICTURE block")
    picture_block_format = {
        "picturetype": 32,
        "MIMEstringlen": 32,
        "MIMEstring": None,
        "descriptionlen": 32,
        "description": None,
        "picwidthpixel": 32,
        "picheightpixel": 32,
        "colourdepthbitsperpixel": 32,
        "indexedcolourpic": 32,
        "picdatalen": 32,
        "picdata": None,
    }
    parsed_picture = {
        "picturetype": None,
        "MIMEstringlen": None,
        "MIMEstring": None,
        "descriptionlen": None,
        "description": None,
        "picwidthpixel": None,
        "picheightpixel": None,
        "colourdepthbitsperpixel": None,
        "indexedcolourpic": None,
        "picdatalen": None,
        "picdata": None,
    }
    blockpos = 0
    nextbytes = picture_block_format.get("picturetype") // 8
    pictype = int(
        "".join(x for x in metablock_data[blockpos : blockpos + nextbytes]), 2
    )
    parsed_picture["picturetype"] = pictype
    blockpos += nextbytes
    nextbytes = picture_block_format.get("MIMEstringlen") // 8
    MIMElen = int(
        "".join(x for x in metablock_data[blockpos : blockpos + nextbytes]), 2
    )
    parsed_picture["MIMEstringlen"] = MIMElen
    picture_block_format["MIMEstring"] = MIMElen * 8
    blockpos += nextbytes
    nextbytes = picture_block_format["MIMEstring"] // 8
    MIMEstring = "".join(
        [chr(int(x, 2)) for x in metablock_data[blockpos : blockpos + nextbytes]]
    )
    parsed_picture["MIMEstring"] = MIMEstring
    blockpos += nextbytes
    nextbytes = picture_block_format.get("descriptionlen") // 8
    descript_len = int(
        "".join(x for x in metablock_data[blockpos : blockpos + nextbytes]), 2
    )
    parsed_picture["descriptionlen"] = descript_len
    picture_block_format["description"] = descript_len * 8
    blockpos += nextbytes
    nextbytes = picture_block_format["description"] // 8
    description = "".join(
        chr(int(x, 2)) for x in metablock_data[blockpos : blockpos + nextbytes]
    )
    parsed_picture["description"] = description
    blockpos += nextbytes
    nextbytes = picture_block_format["picwidthpixel"] // 8
    widthpixel = int(
        "".join(x for x in metablock_data[blockpos : blockpos + nextbytes]), 2
    )
    parsed_picture["picwidthpixel"] = widthpixel
    blockpos += nextbytes
    nextbytes = picture_block_format["picheightpixel"] // 8
    heightpixel = int(
        "".join(x for x in metablock_data[blockpos : blockpos + nextbytes]), 2
    )
    parsed_picture["picheightpixel"] = heightpixel
    blockpos += nextbytes
    nextbytes = picture_block_format["colourdepthbitsperpixel"] // 8
    colourdepth = int(
        "".join(x for x in metablock_data[blockpos : blockpos + nextbytes]), 2
    )
    parsed_picture["colourdepthbitsperpixel"] = colourdepth
    blockpos += nextbytes
    nextbytes = picture_block_format["indexedcolourpic"] // 8
    indexedcolour = int(
        "".join(x for x in metablock_data[blockpos : blockpos + nextbytes]), 2
    )
    parsed_picture["indexedcolourpic"] = indexedcolour
    blockpos += nextbytes
    nextbytes = picture_block_format["picdatalen"] // 8
    datalen = int(
        "".join(x for x in metablock_data[blockpos : blockpos + nextbytes]), 2
    )
    parsed_picture["picdatalen"] = datalen
    picture_block_format["picdata"] = datalen * 8
    blockpos += nextbytes
    nextbytes = picture_block_format["picdata"] // 8
    data = [x for x in metablock_data[blockpos : blockpos + nextbytes]]
    # careful adding binary picdata to printed output, it's huge
    parsed_picture["picdata"] = data
    blockpos += nextbytes
    total_block_length = len(metablock_data)
    if blockpos != total_block_length:
        print(
            f"Warning: only {blockpos} bytes read of {total_block_length} bytes received in picture block parser"
        )
    return parsed_picture


def meta_headerparser(file_data, start_pos=0):
    """reads in file data and calls appropriate metablock handlers for each 
       blocktype encountered
       """
    blockhandler = {
        0: meta_streamparser,
        3: meta_seekparser,
        4: meta_vorbisparser,
        6: meta_pictureparser,
    }
    parsed_metadata = {}
    flac_check = confirm_flac(file_data)
    print(f"File is of type: {flac_check}")
    cur_pos = start_pos + 4
    header_size = 0
    header_format = []
    for k, v in metaheader_block_format.items():
        header_size += v
        header_format.append(v)
    header_size = header_size // 8
    header_format = tuple(header_format)
    ismeta = True
    while ismeta:
        header = file_data[cur_pos : cur_pos + header_size]
        cur_pos += header_size
        header_1string = "".join(byte for byte in header)
        string_pos = 0
        parsed_header = []
        for section in header_format:
            parsed_header.append(header_1string[string_pos : string_pos + section])
            string_pos += section
        # print(parsed_header)
        if parsed_header[0] == "1":
            ismeta = False
        metadata_key = int(parsed_header[1], 2)
        metadata_type = blocktype.get(metadata_key)
        metadata_size = int(parsed_header[2], 2)
        metadata = file_data[cur_pos : cur_pos + metadata_size]
        handler = blockhandler.get(metadata_key)
        if handler is not None:
            parsed_metadata[metadata_type] = handler(metadata)
        else:
            print(f"No appropriate parser for {blocktype.get(metadata_key)} block.")
        cur_pos += metadata_size
    end_pos = cur_pos
    return (end_pos, parsed_metadata)


INPUT_FILEPATH = "~/Desktop/40fighting.flac"
# INPUT_FILEPATH = "~/Desktop/forshovelry.flac"
FILE_DATA = read_file(INPUT_FILEPATH)
METADATA = meta_headerparser(FILE_DATA)
FILELOC = METADATA[0]
TOTAL_FILESIZE = len(FILE_DATA)
PARSED_METADATA = METADATA[1]
print(f"Script ended at byte {FILELOC} of {TOTAL_FILESIZE}")
PICTUREDATA = PARSED_METADATA["PICTURE"]["picdata"]
PARSED_METADATA["PICTURE"]["picdata"] = "lots of binary data, handle it elsewhere"
print(PARSED_METADATA)

# BINARY_PICTUREDATA = [int(x, 2) for x in PICTUREDATA]
# BINARY_PICTUREDATA = [hex(x) for x in BINARY_PICTUREDATA]
# BINARY_PICTUREDATA = [bytes.fromhex(x) for x in BINARY_PICTUREDATA]
# BINARY_PICTUREDATA = binascii.unhexlify(b"".join(BINARY_PICTUREDATA))

# print(BINARY_PICTUREDATA[:10])
# picture = Image.open(PICTUREDATA)
# picture.show()
