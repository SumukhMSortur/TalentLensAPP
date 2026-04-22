import argparse
import os
import shutil


DEFAULT_CLASSES = ["squat", "push-up", "pull up"]


def parse_args():
    parser = argparse.ArgumentParser(
        description="Copy selected exercise folders into dataset/videos.",
    )
    parser.add_argument(
        "source",
        help="Path to the dataset root that contains exercise folders.",
    )
    parser.add_argument(
        "--destination",
        default=os.path.join("dataset", "videos"),
        help="Destination folder for copied videos. Defaults to dataset/videos.",
    )
    parser.add_argument(
        "--classes",
        nargs="+",
        default=DEFAULT_CLASSES,
        help="Case-insensitive class name fragments to match.",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    source = args.source
    destination = args.destination
    required_classes = [name.lower() for name in args.classes]

    if not os.path.isdir(source):
        raise FileNotFoundError(f"Source folder not found: {source}")

    os.makedirs(destination, exist_ok=True)
    copied_count = 0

    for folder in sorted(os.listdir(source)):
        folder_path = os.path.join(source, folder)
        if not os.path.isdir(folder_path):
            continue

        folder_name = folder.lower()
        if not any(class_name in folder_name for class_name in required_classes):
            continue

        dest_path = os.path.join(destination, folder)
        print(f"Copying {folder} -> {dest_path}")
        shutil.copytree(folder_path, dest_path, dirs_exist_ok=True)
        copied_count += 1

    print(f"Dataset copy completed. Copied {copied_count} folder(s).")


if __name__ == "__main__":
    main()
