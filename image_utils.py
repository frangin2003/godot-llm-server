import base64

def image_url_to_data_url(image_url):
    with open(image_url, 'rb') as image_file:
        image_binary = image_file.read()
    return binary_to_data_url(image_binary)

# Function to convert binary image data to base64 and then to data URL
def binary_to_data_url(binary_image, mime_type='image/png', debug=False):
    base64_image = base64.b64encode(binary_image).decode('utf-8')
    if debug:
        with open('image_in_base64.txt', 'w') as file:
            file.write(base64_image)
    return f"data:{mime_type};base64,{base64_image}"
