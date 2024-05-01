import base64
from PIL import Image
import io

def image_url_to_data_url(image_url):
    with open(image_url, 'rb') as image_file:
        image_binary = image_file.read()
    image_binary = resize_image_to_max_dimensions(image_binary)
    # Save the resized image to a file named 'resized.png'
    with open('resized.png', 'wb') as f:
        f.write(image_binary)
    return binary_to_data_url(image_binary)

# Function to convert binary image data to base64 and then to data URL
def binary_to_data_url(binary_image, mime_type='image/png', debug=False):
    base64_image = base64.b64encode(binary_image).decode('utf-8')
    if debug:
        with open('image_in_base64.txt', 'w') as file:
            file.write(base64_image)
    return f"data:{mime_type};base64,{base64_image}"

def resize_image_to_max_dimensions(binary_image, max_width=800, max_height=600):
    # Load the image from binary data
    image = Image.open(io.BytesIO(binary_image))
    
    # Get current dimensions
    original_width, original_height = image.size
    
    # Calculate the new dimensions maintaining the aspect ratio
    ratio = min(max_width / original_width, max_height / original_height)
    new_width = int(original_width * ratio)
    new_height = int(original_height * ratio)
    
    # Resize the image
    resized_image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
    
    # Save the resized image to a binary stream
    img_byte_arr = io.BytesIO()
    resized_image.save(img_byte_arr, format=image.format)
    
    # Return the binary data of the resized image
    return img_byte_arr.getvalue()
