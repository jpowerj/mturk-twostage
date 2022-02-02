# Just takes the folders full of images (in the public_html directory) and
# splits them into batches ready to be piped into the MTurk HIT requests

import os
import csv

output_filename = "./allbatches.csv"
output_header = ["batch_id","offer_amt","image1_url","image2_url","image3_url","image4_url","image5_url"]

known_yes = "http://textlab.econ.columbia.edu/~jjacobs/mturk/MD/MDM432_300-0219.jpg"

offer_amt = "0.15"

root_url = "http://textlab.econ.columbia.edu/~jjacobs/mturk"
mturk_folder = "../public_html/mturk"
state_folders = os.listdir(mturk_folder)
state_folders = [f for f in state_folders if os.path.isdir(mturk_folder + "/" + f)]
total_num = 0
image_counter = 0
batch_counter = 1
batch_list = []
cur_batch = []
for state in state_folders:
  cur_state_folder = mturk_folder + "/" + state
  state_images = os.listdir(cur_state_folder)
  num_images = len(state_images)
  total_num = total_num + num_images
  for img in state_images:
    cur_batch.append(root_url + "/" + state + "/" + img)
    image_counter = image_counter + 1
    if image_counter == 5:
      cur_batch = [batch_counter, offer_amt] + cur_batch
      batch_list.append(cur_batch)
      cur_batch = []
      batch_counter = batch_counter + 1
    elif image_counter == 9:
      cur_batch.append(known_yes)
      cur_batch = [batch_counter, offer_amt] + cur_batch
      batch_list.append(cur_batch)
      cur_batch = []
      image_counter = 0
      batch_counter = batch_counter + 1
print(total_num)

if image_counter != 0 and image_counter != 5:
  cur_batch = [batch_counter, offer_amt] + cur_batch
  batch_list.append(cur_batch)

with open(output_filename, 'w', newline='') as f:
  writer = csv.writer(f)
  writer.writerow(output_header)
  writer.writerows(batch_list)