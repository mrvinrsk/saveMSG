import argparse
import os
from msg_parser import MsOxMessage
from PIL import Image
import mimetypes


def parse_spaces(s):
    return s.split()


def parse_cli_args():
    # Create an ArgumentParser object
    parser = argparse.ArgumentParser()

    # Register custom parameters here
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--file", help="Der Pfad zur Datei")
    group.add_argument("--folder", help="Pfad zum Ordner (nicht rekursiv)")
    group.add_argument("--files", help="Mehrere Datei-Pfade, \"Pfad1 Pfad2 ...\"", type=parse_spaces)

    parser.add_argument("-r", help="Rekursiv suchen", action="store_const", const=True)
    parser.add_argument("-o", help="Output Pfad (wenn abweichend von Downloads)")

    # Parse the command-line arguments
    args = parser.parse_args()

    # Create a dictionary to store parameter values
    params = {}

    # Loop through all custom parameters and save their values in the dictionary
    for arg in vars(args):
        if getattr(args, arg) is not None:
            params[arg] = getattr(args, arg)

    return params


def extract_attachment_data(msg_path):
    # Open the .msg file as a binary file
    with open(msg_path, 'rb') as msg_file:
        # Read the contents of the file into a byte string
        msg_data = msg_file.read()

    # Find the start and end positions of the attachment data in the byte string
    start_pos = msg_data.find(b'\xff\xd8\xff\xe0')
    attachment_data_list = []
    while start_pos >= 0:
        end_pos = msg_data.find(b'\xff\xd9', start_pos)
        attachment_data = msg_data[start_pos:end_pos+2]
        attachment_data_list.append(attachment_data)
        start_pos = msg_data.find(b'\xff\xd8\xff\xe0', end_pos)

    return attachment_data_list


def extract_image_attachments(msg_path, output_dir):
    attachment_data_list = extract_attachment_data(msg_path)

    # Save each image attachment to a separate file with the appropriate file extension based on its MIME type
    for i, attachment_data in enumerate(attachment_data_list):
        mime_type = 'image/jpeg'  # Default MIME type
        if attachment_data.startswith(b'\x89PNG\r\n\x1a\n'):
            mime_type = 'image/png'
        elif attachment_data.startswith(b'GIF89a') or attachment_data.startswith(b'GIF87a'):
            mime_type = 'image/gif'
        elif attachment_data.startswith(b'\xff\xd8'):
            mime_type = 'image/jpeg'
        elif attachment_data.startswith(b'%PDF'):
            mime_type = 'application/pdf'
        elif attachment_data.startswith(b'RIFF') and attachment_data[8:12] == b'WEBP':
            mime_type = 'image/webp'

        file_extension = mimetypes.guess_extension(mime_type)

        if file_extension is not None and mime_type.startswith('image/'):
            file_name = f'attachment_{i}{file_extension}'
            file_path = os.path.join(output_dir, file_name)
            with open(file_path, 'wb') as attachment_file:
                attachment_file.write(attachment_data)


if __name__ == "__main__":
    arguments = parse_cli_args()
    save_path = os.path.expanduser("~/Downloads")

    if "o" in arguments:
        save_path = arguments["o"]

        # Create folder, if it does not exist
        os.makedirs(save_path, exist_ok=True)

    msg_files = []
    if "file" in arguments:
        msg_files.append(arguments["file"])

    if "files" in arguments:
        msg_files.append(arguments["files"])
        for file in arguments["files"]:
            if file.endswith(".msg"):
                msg_files.append(file)
            else:
                print(str(file) + " ist keine .msg-Datei.")

    if "folder" in arguments:
        all_files = os.listdir(arguments["folder"])

        if "r" in arguments:
            for root, dirs, files in os.walk(arguments["folder"]):
                for file in files:
                    if file.endswith(".msg"):
                        msg_files.append(os.path.join(root, file))

        else:
            for file in all_files:
                if file.endswith(".msg"):
                    msg_files.append(os.path.join(arguments["folder"], file))

    if len(msg_files) >= 1:
        print("Found " + str(len(msg_files)) + " msg file" + ("s" if len(msg_files) != 1 else ""))

    for file in msg_files:
        print("Searching for attachments in " + str(file))
        extract_image_attachments(file, save_path)
