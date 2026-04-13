import numpy as np
import os
import matplotlib.pyplot as plt

# Change class name if needed
class_name = "squat"

feature_folder = f"dataset/features/{class_name}"

file = os.listdir(feature_folder)[0]

data = np.load(os.path.join(feature_folder, file))

print("Feature Shape:", data.shape)
print("\nFirst 10 Frames:\n")
print(data[:10])


# Plot Features
plt.figure(figsize=(10,5))

plt.plot(data[:,0], label="Left Knee Angle")
plt.plot(data[:,1], label="Right Knee Angle")

plt.legend()
plt.title("Feature Visualization")
plt.xlabel("Frames")
plt.ylabel("Angle")

plt.show() 