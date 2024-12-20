import os, json, re
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
    
    properties = {}  # Extract key information
    node_reference = globals()['Reference']
    for att_array in node_reference.__all_properties__: 
            attr = att_array[0]
            entry = bib_database.entries[0]    
            if attr == "type":
                properties[attr] = entry.get('ENTRYTYPE')
            elif attr == "authors":
                # Split the string on " and "
                authors_list = entry.get('author').split(" and ")
                # Clean up each part and format the output
                properties[attr] = [author.replace(',', '').strip() for author in authors_list]
                print(properties[attr])
            elif attr == "published_name":
                properties[attr] = entry.get('journal')
            elif attr == "doi":                
                doi_pattern = r'10\.\d{4,9}/[-._;()/:A-Z0-9]+'    # Regular expression pattern for DOI
                doi_match = re.search(doi_pattern, entry.get('doi'), re.IGNORECASE)                
                properties[attr] = doi_match.group(0) if doi_match else None
            elif attr == "published_date":
                properties[attr] = entry.get('year')
            else:
                properties[attr] = entry.get(attr)

    print(properties)
     # Create the JSON template
    json_bib = {node_reference.__name__: {"properties": properties,}}
    
    json_bibfile = json.dumps(json_bib, indent=4, ensure_ascii=False)
    print(json_bibfile)
    # Write to a JSON file
    save_path = os.path.abspath(os.path.dirname(bibfile))
    with open(os.path.join(save_path, f'Reference.json'), 'w', encoding='utf-8') as json_file:
        json_file.write(json_bibfile)
    


if __name__ == '__main__':

    bib2json("./data/pericles_1614684012.bib")
    
    # fp = read_files()
    # for file in fp:
    #     print(file)


