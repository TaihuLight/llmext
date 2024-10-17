import os
import bibtexparser
from hub_entity import Reference

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



# Read a bibtex file to generate a json file for a reference entity
def bib2json(bibfile):
    with open(bibfile, 'r') as bibtex_file:
        bib_database = bibtexparser.load(bibtex_file)

    # Extract key information
    entries = []

    node_reference = globals()['Reference']
    for att_array in node_class.__all_properties__: 
          attr = att_array[0]
          property_obj = getattr(node_class, attr)


    for entry in bib_database.entries:
        entry_info = {
            'key': entry.get('ID'),
            'title': entry.get('title'),
            'author': entry.get('author'),
            'year': entry.get('year')
        }
        entries.append(entry_info)
    
    return entries


if __name__ == '__main__':
    
    fp = read_files()
    for file in fp:
        print(file)


