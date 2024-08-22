import os
from skimage import io, transform
import numpy as np
from PIL import Image
from pathlib import Path
from skimage.filters import threshold_local
import pandas as pd

# User-defined parameters (adjust as necessary)
root_directory = input("Enter the path to your root directory containing the images: ")
central_output_folder = input("Enter the path to your central output directory: ")
consolidated_csv_path = os.path.join(central_output_folder, 'consolidated_results.csv')

def is_valid_image_file(file_path):
    try:
        if not file_path.endswith('.tif'):
            return False
        img = io.imread(file_path)
        if img is None or img.size == 0:
            return False
        return True
    except Exception as e:
        print(f"Invalid or corrupted file detected: {file_path}, Error: {e}")
        return False

def apply_bf_adaptive_threshold_inverted(bf_image, block_size=35, offset=10):
    adaptive_thresh = threshold_local(bf_image, block_size, offset=offset)
    bf_thresholded = bf_image > adaptive_thresh
    bf_thresholded = bf_thresholded.astype(np.uint8) * 255
    
    # Invert the threshold to remove inner fill and keep only the bone outline
    inverted_mask = np.invert(bf_thresholded.astype(bool))

    # Convert BF to RGBA and make the inner fill transparent, with bone outlines in black
    bf_rgba = np.zeros((*bf_image.shape, 4), dtype=np.uint8)
    bf_rgba[inverted_mask, :3] = 0  # Set bone outlines to black
    bf_rgba[inverted_mask, 3] = 255  # Set alpha channel to fully opaque for bone outlines

    return bf_rgba

def ensure_rgba(image):
    if image.ndim == 2:  # If grayscale, convert to RGB
        image = np.stack([image, image, image], axis=-1)
    if image.shape[-1] == 3:  # If RGB, add alpha channel
        alpha_channel = np.full(image.shape[:2], 255, dtype=np.uint8)
        image = np.dstack((image, alpha_channel))
    return image.astype(np.uint8)

def create_colored_overlay(mask, color):
    overlay = np.zeros((*mask.shape, 4), dtype=np.uint8)
    overlay[mask > 0, :3] = color  # Apply color only where the mask is non-zero
    overlay[mask > 0, 3] = 255  # Fully opaque where the mask is non-zero
    return overlay

def enhance_colors(image, color_factors):
    enhanced_image = image[..., :3] * color_factors
    enhanced_image = np.clip(enhanced_image, 0, 255)  # Ensure values stay within the valid range
    return np.dstack((enhanced_image, image[..., 3]))  # Preserve the alpha channel

def blend_images(base_image, overlay_image, alpha=0.5):
    overlay_rgb = overlay_image[..., :3]
    overlay_alpha = overlay_image[..., 3:] / 255.0  # Normalize alpha channel
    
    blended_image = (1 - overlay_alpha) * base_image[..., :3] + overlay_alpha * overlay_rgb
    alpha_channel = base_image[..., 3:]
    return np.dstack((blended_image.astype(np.uint8), alpha_channel))

def calculate_intersections(uw_map, col10_map, twist_map):
    uw_col10_intersection = np.logical_and(uw_map > 0, col10_map > 0).astype(np.uint8)
    uw_twist_intersection = np.logical_and(uw_map > 0, twist_map > 0).astype(np.uint8)
    col10_twist_intersection = np.logical_and(col10_map > 0, twist_map > 0).astype(np.uint8)
    all_intersections_of_all = np.logical_and(uw_col10_intersection > 0, twist_map > 0).astype(np.uint8)
    
    uw_col10_count = np.count_nonzero(uw_col10_intersection)
    uw_twist_count = np.count_nonzero(uw_twist_intersection)
    col10_twist_count = np.count_nonzero(col10_twist_intersection)
    all_intersections_count = np.count_nonzero(all_intersections_of_all)
    
    return uw_col10_count, uw_twist_count, col10_twist_count, all_intersections_count

def process_image_pair(bf_image_path, uw_image_path, col10_image_path, twist_image_path, output_dir, block_size=35, offset=10):
    try:
        base_name = Path(bf_image_path).stem
        parent_folder = os.path.basename(os.path.dirname(bf_image_path))

        bf_image = io.imread(bf_image_path)
        uw_image = io.imread(uw_image_path)
        col10_image = io.imread(col10_image_path)
        twist_image = io.imread(twist_image_path)
        
        bf_image = bf_image.astype(np.uint8)
        uw_image = uw_image.astype(np.uint8)
        col10_image = col10_image.astype(np.uint8)
        twist_image = twist_image.astype(np.uint8)

        if bf_image.ndim != 2 or uw_image.ndim != 2 or col10_image.ndim != 2 or twist_image.ndim != 2:
            raise ValueError("Unsupported image format. Images must be 2D greyscale.")

        if uw_image.shape != bf_image.shape:
            uw_image = transform.resize(uw_image, bf_image.shape, preserve_range=True)
        if col10_image.shape != bf_image.shape:
            col10_image = transform.resize(col10_image, bf_image.shape, preserve_range=True)
        if twist_image.shape != bf_image.shape:
            twist_image = transform.resize(twist_image, bf_image.shape, preserve_range=True)

        bf_thresholded = apply_bf_adaptive_threshold_inverted(bf_image, block_size=block_size, offset=offset)

        density_uw = uw_image.astype(float) / 255.0
        density_col10 = col10_image.astype(float) / 255.0
        density_twist = twist_image.astype(float) / 255.0

        uw_threshold = np.mean(density_uw) + 0.5 * np.std(density_uw)
        col10_threshold = np.mean(density_col10) + 0.5 * np.std(density_col10)
        twist_threshold = np.mean(density_twist) + 0.5 * np.std(density_twist)
        uw_density_map = np.where(density_uw > uw_threshold, density_uw, 0)
        col10_density_map = np.where(density_col10 > col10_threshold, density_col10, 0)
        twist_density_map = np.where(density_twist > twist_threshold, density_twist, 0)

        uw_colored = np.zeros((*uw_image.shape, 4), dtype=np.float32)
        col10_colored = np.zeros((*col10_image.shape, 4), dtype=np.float32)
        twist_colored = np.zeros((*twist_image.shape, 4), dtype=np.float32)

        uw_colored[..., 2] = uw_density_map
        uw_colored[..., 3] = uw_density_map

        col10_colored[..., 1] = col10_density_map
        col10_colored[..., 3] = col10_density_map

        twist_colored[..., 0] = twist_density_map
        twist_colored[..., 3] = twist_density_map

        uw_col10_overlay = np.maximum(uw_colored, col10_colored)
        uw_twist_overlay = np.maximum(uw_colored, twist_colored)
        intersection_overlay = np.maximum(uw_col10_overlay, uw_twist_overlay)

        combined_overlay = np.maximum.reduce([uw_colored, col10_colored, twist_colored, intersection_overlay])

        color_factors = np.array([1.5, 1.5, 1.5])
        enhanced_combined_overlay = enhance_colors(combined_overlay, color_factors)
        
        bf_rgba = apply_bf_adaptive_threshold_inverted(bf_image, block_size=block_size, offset=offset)
        overlays = [uw_colored, col10_colored, twist_colored]
        final_combined_image = blend_images(bf_rgba, enhanced_combined_overlay)

        os.makedirs(output_dir, exist_ok=True)
        Image.fromarray((uw_colored * 255).astype(np.uint8)).save(os.path.join(output_dir, f'{base_name}-uw-overlay.tif'))
        Image.fromarray((col10_colored * 255).astype(np.uint8)).save(os.path.join(output_dir, f'{base_name}-col10-overlay.tif'))
        Image.fromarray((twist_colored * 255).astype(np.uint8)).save(os.path.join(output_dir, f'{base_name}-twist-overlay.tif'))
        Image.fromarray((intersection_overlay * 255).astype(np.uint8)).save(os.path.join(output_dir, f'{base_name}-intersection-overlay.tif'))
        Image.fromarray(final_combined_image).save(os.path.join(output_dir, f'{base_name}-final-combined.tif'))

        uw_col10_count, uw_twist_count, col10_twist_count, all_intersections_count = calculate_intersections(
            uw_density_map, col10_density_map, twist_density_map)

        csv_entry = {
            'Parent Folder': parent_folder,
            'BF Total': np.count_nonzero(bf_image > 0),
            'UW Total': np.count_nonzero(uw_image > 0),
            'Col10 Total': np.count_nonzero(col10_image > 0),
            'Twist Total': np.count_nonzero(twist_image > 0),
            'uw-Col10 Intersection': uw_col10_count,
            'uw-Twist Intersection': uw_twist_count,
            'Col10-Twist Intersection': col10_twist_count, 
            'All Intersections': all_intersections_count
        }
        
        return csv_entry, final_combined_image
    except Exception as e:
        print(f"Error processing image pair {bf_image_path}: {e}")
        return None, None

def process_all_images(root_dir, output_dir):
    csv_entries = []
    for subdir, _, files in os.walk(root_dir):
        bf_files = [f for f in files if f.endswith('.tif') and '_BF_' in f and is_valid_image_file(os.path.join(subdir, f))]
        for bf_file in bf_files:
            bf_image_path = os.path.join(subdir, bf_file)

            uw_files = [f for f in files if '_UW_' in f and f.endswith('.tif') and is_valid_image_file(os.path.join(subdir, f))]
            col10_files = [f for f in files if '_Col10_' in f and f.endswith('.tif') and is_valid_image_file(os.path.join(subdir, f))]
            twist_files = [f for f in files if '_Twist_' in f and f.endswith('.tif') and is_valid_image_file(os.path.join(subdir, f))]

            if not uw_files or not col10_files or not twist_files:
                print(f"Missing UW, Col10, or Twist images for BF file {bf_file}")
                continue

            uw_path = os.path.join(subdir, uw_files[0])
            col10_path = os.path.join(subdir, col10_files[0])
            twist_path = os.path.join(subdir, twist_files[0])

            fish_output_dir = os.path.join(output_dir, Path(bf_image_path).stem)
            os.makedirs(fish_output_dir, exist_ok=True)
            
            csv_entry, final_image = process_image_pair(
                bf_image_path, uw_path, col10_path, twist_path, fish_output_dir)
            
            if csv_entry is not None:
                csv_entries.append(csv_entry)

    if csv_entries:
        df = pd.DataFrame(csv_entries)
        df.to_csv(consolidated_csv_path, index=False)
        print(f"CSV file saved to {consolidated_csv_path}")

# Execution starts here
os.makedirs(central_output_folder, exist_ok=True)
process_all_images(root_directory, central_output_folder)
