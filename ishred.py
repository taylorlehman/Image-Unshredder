import sys
from PIL import Image
import math

#****************************
#         Classes
#****************************
class edge:
	def __init__(self, x):
		self.x_index = x
		
class shard:
	def __init__(self, lower, upper, shard_num):
		self.lower_edge = edge(lower)
		self.upper_edge = edge(upper)
		self.shard_number = shard_num
	has_lower_match = 0
	
#****************************
#         Functions
#****************************

#Get the RGBA tuple for one pixel
def get_pixel_value(x, y):
	pixel = DATA[y * WIDTH + x]
	return pixel

#Compare the value of two pixels to determine
#if they are a potential match - returns 1 if they
#are and 0 if they are not
def compare_two_pixels(p1, p2, x1, x2, y):
	p1brightness = math.sqrt(.241*p1[0]*p1[0] + .691*p1[1]*p1[1] + .068*p1[2]*p1[2])
	p2brightness = math.sqrt(.241*p2[0]*p2[0] + .691*p2[1]*p2[1] + .068*p2[2]*p2[2])
	if math.fabs(p1brightness-p2brightness) < 10:
		return 0
	else:
		return 1

#Compare two edges to determine if they are a potential match
def compare_two_edges(e1index, e2index):
	non_matching_pixel_count = 0
	#loop through each pixel in the y space
	for pixel_y_index in range(0,HEIGHT):
		pixel1 = get_pixel_value(e1index, pixel_y_index)
		pixel2 = get_pixel_value(e2index, pixel_y_index)
		non_matching_pixel_count = non_matching_pixel_count + compare_two_pixels(pixel1, pixel2, e1index, e2index, pixel_y_index)
	return non_matching_pixel_count
	
#****************************
#     Main Program Flow
#****************************

#open the image and get it's data
IMAGE = Image.open(sys.argv[1])
DATA = IMAGE.getdata()
WIDTH, HEIGHT = IMAGE.size
SHARD_WIDTH = 32
SHARD_COUNT = WIDTH/SHARD_WIDTH

#Build a list of shard objects
base_vec = [0, 31]
i = 0
SHARDS = []
while i < SHARD_COUNT:
	SHARDS.append(shard(32 * i + base_vec[0], 32 * i + base_vec[1], i))
	i = i + 1

#loop through the shards finding a match for each edge
first_shard = SHARDS[0]
temp_shard_value = 0
for shard in SHARDS:
	le_non_matches = HEIGHT
	ue_non_matches = HEIGHT
	#For this particular shard, compare each of it's
	#edges to every other shard edge
	for shard2 in SHARDS:
		#make sure it's not the current shard from the outer loop
		if shard != shard2:
			#Only makes sense to compare the lower edge of one shard with the upper edge of another
			temp_le_non_matches = compare_two_edges(shard.lower_edge.x_index, shard2.upper_edge.x_index)
			if temp_le_non_matches < le_non_matches:
				if temp_le_non_matches < 1*HEIGHT:
					le_non_matches = temp_le_non_matches
					shard.lower_edge_match_shard = shard2
					shard.lower_edge_value = le_non_matches
			
			#Only makes sense to compare the lower edge of one shard with the upper edge of another
			temp_ue_non_matches = compare_two_edges(shard.upper_edge.x_index, shard2.lower_edge.x_index)
			if temp_ue_non_matches < ue_non_matches:
				#If the second shard already has a match for it's lower edge, we don't want to re-assign it
				if shard2.has_lower_match == 0:
					ue_non_matches = temp_ue_non_matches
					shard.upper_edge_match_shard = shard2
	#We want to figure out what shard goes first.  The shard with 
	#the highest number of non-matches on the lower edge is the first shard.
	if shard.lower_edge_value > temp_shard_value:
		temp_shard_value = shard.lower_edge_value
		first_shard = shard
	
	#When we've completed a pass, we know we've found a lower match for the shard
	shard.upper_edge_match_shard.has_lower_match = 1
	
#rebuild the new image
counter = 0
unshredded = Image.new("RGBA", IMAGE.size)
current_shard = first_shard
#loop through each shard
while counter < SHARD_COUNT:
	x1,y1 = SHARD_WIDTH * current_shard.shard_number, 0
	x2,y2 = x1+SHARD_WIDTH, HEIGHT
	source_shard = IMAGE.crop((x1,y1,x2,y2))
	destination_point = (SHARD_WIDTH*counter,0)
	unshredded.paste(source_shard, destination_point)
	current_shard = current_shard.upper_edge_match_shard
	counter = counter + 1
unshredded.save("unshredded.png","PNG")