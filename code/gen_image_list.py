import os
import csv

url_list = []

output_filename = "./all_images.csv"

root_url = "http://textlab.econ.columbia.edu/~jjacobs/mturk"
mturk_folder = "../public_html/mturk"
state_folders = os.listdir(mturk_folder)
state_folders = [f for f in state_folders if os.path.isdir(mturk_folder + "/" + f)]
# Uncomment to list only 1860 images
#state_folders = [f for f in state_folders if "1860" in f]

total_num_images = 0
for cur_folder in state_folders:
  cur_folder_full = mturk_folder + "/" + cur_folder
  cur_images = os.listdir(cur_folder_full)
  num_images = len(cur_images)
  total_num_images = total_num_images + num_images
  cur_urls = [(root_url + "/" + cur_folder + "/" + img) for img in cur_images]
  cur_urls = [[url] for url in cur_urls]
  url_list.extend(cur_urls)
  
with open(output_filename, 'w', newline='') as f:
  writer = csv.writer(f)
  writer.writerows(url_list)

print(total_num_images)