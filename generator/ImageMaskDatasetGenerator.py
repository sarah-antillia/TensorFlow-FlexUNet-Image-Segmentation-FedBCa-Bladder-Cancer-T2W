# Copyright 2026 antillia.com Toshiyuki Arai
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# ImageMaskDatasetGenerator.py
# 2026/09/22

import os
import cv2
import glob
import nibabel as nib
import shutil
import traceback
import numpy as np

import traceback

class ImageMaskDatasetGenerator:
  def __init__(self, resize=512):
    self.RESIZE         = (resize,resize)
    #self.ROTATION   = cv2.ROTATE_90_COUNTERCLOCKWISE
    self.ROTATION   = cv2.ROTATE_90_CLOCKWISE
    # cancer mask color = dark_red
    self.MASK_BGR_COLOR = (20,20,180)

  
  def colorize_mask(self, mask):
     h, w = mask.shape[:2]
     colorized = np.zeros((h, w, 3), dtype=np.uint8)
     colorized[np.equal(mask, 1)] = self.MASK_BGR_COLOR
     return colorized

  def normalize(self, data):
    min = data.min()
    max = data.max()
    
    if max - min != 0:
        normalized = ((data - min) / (max - min) * 255).astype(np.uint8)
    else:
        normalized = np.zeros_like(data, dtype=np.uint8)
    return normalized

  def get_mask_slice(self, data, i):
    slice = data[:, :, i]
    slice = cv2.rotate(slice, self.ROTATION)
    slice = cv2.resize(slice, self.RESIZE)
    valid = False
    if slice.any() >0:
       valid = True
    return valid, slice

  def get_image_slice(self, data, i):
    slice = data[:, :, i]
    slice = self.normalize(slice)
    slice = cv2.rotate(slice, self.ROTATION)
    slice = cv2.resize(slice, self.RESIZE)
    return slice

  def generate(self, data_dir, output_images_dir, output_masks_dir):
    centers = os.listdir(data_dir)
    for center in centers:
       center_fullpath = os.path.join(data_dir, center)
       images_dir = os.path.join(center_fullpath, "T2WI")
       masks_dir  = os.path.join(center_fullpath, "Annotation")
       self.generate_one(center, images_dir, masks_dir, output_images_dir, output_masks_dir)
  
  def generate_one(self, center, images_dir, masks_dir, output_images_dir, output_masks_dir):
     self.output_images_dir = output_images_dir
     self.output_masks_dir  = output_masks_dir
  
     image_files = sorted(glob.glob(images_dir + "/*.nii.gz"))
     n = len(image_files)
     print("Number of imagefiles ", n)

     mask_files = sorted(glob.glob(masks_dir + "/*.nii.gz"))
     m = len(mask_files)
     print("Number of mask_files ", m)
  
     num = n
     case_index = 10000
     for i in range(num):
       case_index += 1
       image_file = image_files[i]
       basename   = os.path.basename(image_file)
       mask_file  = os.path.join(masks_dir, basename)
       if not os.path.exists(mask_file):
          # This happens some times, so skip this case.
          print("Not found mask_file ", mask_file)
          continue
       
       image_data = nib.load(image_file).get_fdata() 
       mask_data  = nib.load(mask_file).get_fdata()  

       num_image_slices = image_data.shape[2]
       num_mask_slices  = mask_data.shape[2]

       if num_image_slices != num_mask_slices:
          # This happens also some times, so skip this case.
          raise Exception("Unmatched the number of image_slices and mask_slices")
       
       for slice_index in range(num_mask_slices):
         image = self.get_image_slice(image_data, slice_index)
         valid, mask = self.get_mask_slice(mask_data, slice_index)
         if valid:
           colorized = self.colorize_mask(mask)
           filename = center + "_" + str(case_index) + "_" + str(slice_index) + ".png"
           output_image_filepath = os.path.join(output_images_dir, filename)
           output_mask_filepath  = os.path.join(output_masks_dir,  filename)
           cv2.imwrite(output_image_filepath, image)
           print("Saved ",output_image_filepath)
           cv2.imwrite(output_mask_filepath,  colorized)
           print("Saved ",output_mask_filepath)
         else:
            print("Skipped the invalid empty mask and the corresponding image---")

if __name__ == "__main__":
  try:
    #Federated Multi-Center Bladder Cancer dataset
    data_dir = "./FedBCa"
 
    output_dir = "./FedBCa-master"
    if os.path.exists(output_dir):
      shutil.rmtree(output_dir)
    output_images_dir = os.path.join(output_dir, "images")
    output_masks_dir  = os.path.join(output_dir,  "masks")
    os.makedirs(output_images_dir)
    os.makedirs(output_masks_dir)

    generator = ImageMaskDatasetGenerator()
    generator.generate(data_dir, output_images_dir, output_masks_dir)

  except:
    traceback.print_exc()


                   
      

