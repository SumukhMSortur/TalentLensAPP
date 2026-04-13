import os
import shutil

source = r"D:\archive (1)"
destination = r"dataset\videos"

required_classes = [
    "squat",
    "push-up",
    "pull up"
]

for folder in os.listdir(source):
    
    folder_path = os.path.join(source, folder)
    
    if os.path.isdir(folder_path):
        
        for cls in required_classes:
            
            if cls in folder.lower():
                
                dest_path = os.path.join(destination, folder)
                
                print(f"Copying {folder}...")
                
                shutil.copytree(folder_path, dest_path, dirs_exist_ok=True)

print("Dataset copied successfully!")