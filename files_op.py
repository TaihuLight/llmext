import os

# Read all the .md files in a directory
def read_files(direct= './archive', ext='.md'):
    # List to hold the paths of .md files
    file_paths = []

    # Walk through the directory
    for root, dirs, files in os.walk(direct):
        for file in files:
            if file.endswith(ext):
                # Append the full path of the .md file
                file_paths.append(os.path.join(root, file))

    return file_paths






if __name__ == '__main__':
    
    fp = read_files()
    for file in fp:
        print(file)


