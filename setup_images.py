<<<<<<< HEAD
import os
import urllib.request

# Image URL (the one you provided earlier)
image_url = "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTbIsacYWfXcged_EXwDDEUR5YULsZiKiriJQ&s"

# Create images directory if it doesn't exist
images_dir = os.path.join(os.path.dirname(__file__), 'static', 'images')
os.makedirs(images_dir, exist_ok=True)

try:
    # Download the image
    print("Downloading milk bottle image...")
    with urllib.request.urlopen(image_url) as response:
        image_data = response.read()
    
    # Save for all three products
    filenames = ['a2-cow-milk.jpg', 'buffalo-milk-gold.jpg', 'buffalo-milk-goldplus.jpg']
    
    for filename in filenames:
        filepath = os.path.join(images_dir, filename)
        with open(filepath, 'wb') as f:
            f.write(image_data)
        print(f"✓ Saved {filename}")
    
    print("\n✓ All images downloaded and saved successfully!")
    
except Exception as e:
    print(f"Error downloading image: {e}")
    print("\nAlternative: Save the attached image manually to:")
    print(f"  {images_dir}\\a2-cow-milk.jpg")
    print(f"  {images_dir}\\buffalo-milk-gold.jpg")
    print(f"  {images_dir}\\buffalo-milk-goldplus.jpg")
=======
import os
import urllib.request

# Image URL (the one you provided earlier)
image_url = "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTbIsacYWfXcged_EXwDDEUR5YULsZiKiriJQ&s"

# Create images directory if it doesn't exist
images_dir = os.path.join(os.path.dirname(__file__), 'static', 'images')
os.makedirs(images_dir, exist_ok=True)

try:
    # Download the image
    print("Downloading milk bottle image...")
    with urllib.request.urlopen(image_url) as response:
        image_data = response.read()
    
    # Save for all three products
    filenames = ['a2-cow-milk.jpg', 'buffalo-milk-gold.jpg', 'buffalo-milk-goldplus.jpg']
    
    for filename in filenames:
        filepath = os.path.join(images_dir, filename)
        with open(filepath, 'wb') as f:
            f.write(image_data)
        print(f"✓ Saved {filename}")
    
    print("\n✓ All images downloaded and saved successfully!")
    
except Exception as e:
    print(f"Error downloading image: {e}")
    print("\nAlternative: Save the attached image manually to:")
    print(f"  {images_dir}\\a2-cow-milk.jpg")
    print(f"  {images_dir}\\buffalo-milk-gold.jpg")
    print(f"  {images_dir}\\buffalo-milk-goldplus.jpg")
>>>>>>> 674038acaea1553ff7758abf94159b647b581115
