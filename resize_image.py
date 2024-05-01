# Import the necessary function from image_utils module
from image_utils import image_url_to_data_url

# Define the path to the image
image_path = "france.png"

# Use the function to convert and resize the image, then get a data URL
data_url = image_url_to_data_url(image_path)

# Print the resulting data URL
print(data_url)