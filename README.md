# VitalVista

VitalVista is a comprehensive image processing toolkit designed for analyzing and visualizing multi-channel fluorescence and brightfield microscopy images. This tool is especially useful for researchers working with `.tif` image files, providing capabilities such as adaptive thresholding, overlay creation, and intersection analysis of fluorescence images.

## Features

- **Adaptive Thresholding**: Apply adaptive thresholding to brightfield images to extract bone outlines and other structures.
- **Overlay Creation**: Generate colored overlays for UW, Col10, and Twist fluorescence channels.
- **Intersection Analysis**: Calculate intersections between different fluorescence channels and analyze them.
- **Image Export**: Save processed images and overlays as `.tif` files.
- **CSV Output**: Export intersection and other image metrics to a consolidated CSV file.

## How to Use

### Directory Structure
- **Root Directory**: Set the root directory where your images are stored in the `root_directory` variable.
- **Central Output Folder**: Define the central output folder for saving processed images and CSV files in the `central_output_folder` variable.

### Image Requirements
- Images should be in `.tif` format.
- Brightfield images should include `_BF_` in their filenames.
- Fluorescence images should include `_UW_`, `_Col10_`, or `_Twist_` in their filenames.

### Key Functions

- **is_valid_image_file(file_path)**: Validates the image file, ensuring it is not corrupted.
- **apply_bf_adaptive_threshold_inverted(bf_image)**: Applies adaptive thresholding to the brightfield image and inverts it to highlight bone outlines.
- **ensure_rgba(image)**: Ensures the image has an RGBA format.
- **create_colored_overlay(mask, color)**: Creates a colored overlay for a given mask.
- **enhance_colors(image, color_factors)**: Enhances the color intensity of the overlay.
- **blend_images(base_image, overlay_image, alpha=0.5)**: Blends the overlay image with the base image.
- **calculate_intersections(uw_map, col10_map, twist_map)**: Calculates intersection areas between different overlays.
- **process_image_pair(bf_image_path, uw_image_path, col10_image_path, twist_image_path, output_dir)**: Processes an image set and saves the results.
- **process_all_images(root_dir, output_dir)**: Processes all images in the root directory and saves the results in the central output folder.

### Customization

- **Threshold Values**: Adjust the thresholds for the UW, Col10, and Twist images within the `process_image_pair` function:
  ```python
  uw_threshold = np.mean(density_uw) + 0.5 * np.std(density_uw)
  col10_threshold = np.mean(density_col10) + 0.5 * np.std(density_col10)
  twist_threshold = np.mean(density_twist) + 0.5 * np.std(density_twist)
  ```
- **Overlay Colors**: Modify the overlay colors in the `process_image_pair` function:
  ```python
  uw_colored[..., 2] = uw_density_map  # Blue channel
  col10_colored[..., 1] = col10_density_map  # Green channel
  twist_colored[..., 0] = twist_density_map  # Red channel
  ```
- **Output Paths**: Change the output paths for images and CSV files by modifying the `central_output_folder` variable and paths in the `process_image_pair` and `process_all_images` functions.

### Example Usage

1. Set the `root_directory` and `central_output_folder` paths in the script.
2. Run the script to process all valid images in the root directory.
3. Check the `central_output_folder` for the output images and CSV file.

### Requirements

- Python 3.x
- numpy
- pandas
- scikit-image
- PIL (Python Imaging Library)

### Installation

Install the required packages using pip:
```bash
pip install numpy pandas scikit-image pillow
```

### License

This project is licensed under the MIT License.

### Contact

For any inquiries or support, please open an issue on the GitHub repository.
