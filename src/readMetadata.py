from PIL import Image
from PIL.ExifTags import TAGS

def read_image_metadata(image_path):
    """
    Reads and prints metadata from the given image.
    """
    try:
        # Open the image file
        image = Image.open(image_path)

        # Extract EXIF data
        exif_data = image._getexif()

        if exif_data is not None:
            metadata = {}
            for tag_id, value in exif_data.items():
                # Get the tag name instead of the tag ID
                tag_name = TAGS.get(tag_id, tag_id)
                metadata[tag_name] = value

            # Print metadata
            for tag, value in metadata.items():
                print(f"{tag}: {value}")
        else:
            print("No EXIF metadata found.")

    except Exception as e:
        print(f"Error reading metadata: {e}")

if __name__ == '__main__':
    #image_path = 'Images/UBER_2.jpeg'
    image_path = 'Images/UBER_V2_1.jpg'
    read_image_metadata(image_path)