from zlib import crc32
import subprocess
import sys

# Max png size to bruteforce for
MAX_WIDTH = 2000
MAX_HEIGHT = 2000

# Turn bytes object into an int with big endian
def bytes_to_int(b):
    return int.from_bytes(b, "big")

# Turn an int into a padded 4-byte bytes object
def int_to_bytes(i):
    return i.to_bytes(2, byteorder='big').rjust(4, '\x00'.encode())

# Find the correct width/height from a given crc
def crack_crc(filedata, target_crc):
	index = 12
	ihdr = bytearray(filedata[index:index+17])
	width_index = 7
	height_index = 11
	for x in range(1, MAX_WIDTH):
		height = bytearray(x.to_bytes(2,'big'))
		for y in range(1, MAX_HEIGHT):
			width = bytearray(y.to_bytes(2,'big'))
			for i in range(len(height)):
				ihdr[height_index - i] = height[-i -1]
			for i in range(len(width)):
				ihdr[width_index - i] = width[-i -1]
			if hex(crc32(ihdr)) == "0x" + target_crc:
				return [width, height]
		for i in range(len(width)):
				ihdr[width_index - i] = bytearray(b'\x00')[0]

# Change the width and height of a given png file object
def change_size(file_object, new_width, new_height):
    file_object.seek(16)
    new_width_bytes = int_to_bytes(new_width)
    new_height_bytes = int_to_bytes(new_height)
    file_object.write(new_width_bytes)
    file_object.write(new_height_bytes)

if __name__ == "__main__":
	# Get input from arguments
	if len(sys.argv) != 3:
		exit("Usage: python fix_png_size.py broken.png fixed.png")
	filename, fixed_filename = sys.argv[1:]
	filedata = open(filename,'rb').read()

	# Get CRC from pngcheck
	try:
		subprocess.check_output(["pngcheck", filename])
		exit("Image dimensions already match CRC.")
	except subprocess.CalledProcessError as e:
		error = e.output.decode()
		if "this is neither a PNG" in error:
			exit("Invalid PNG file.")
		elif "CRC error in chunk IHDR" not in error:
			exit("Image dimensions already match CRC.")
		crc = error.split("expected ")[1].split(")")[0]

	# Crack CRC
	print(f"Cracking {filename} for CRC {crc}...")
	bytes_width, bytes_height = crack_crc(filedata, crc)
	width, height = [bytes_to_int(bytes_width), bytes_to_int(bytes_height)]
	print(f"Found size {width}x{height}!")

	# Write new size into file
	with open(fixed_filename, "w+b") as f:
		# Copy current data
		f.write(filedata)
		f.seek(0)
		# Edit size
		change_size(f, width, height)
	
	# Complete
	print(f"Fixed file written to {fixed_filename}.")
