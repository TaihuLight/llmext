"""
Extract experimental describtion from the HTML file and convert it to markdown and text files

Used Libraries:
[markdownify] https://pypi.org/project/markdownify/
[doi2bibtex] https://github.com/timothygebhard/doi2bibtex

@author: LIAO LONGLONG 2024-11-8
"""

import glob, os, re
from os.path import join
from bs4 import BeautifulSoup
from markdownify import MarkdownConverter   # Convert HTML to markdown, see https://github.com/AI4WA/Docs2KG
from neomodel import StructuredNode, StringProperty, ArrayProperty, DateTimeProperty
from doi2bibtex.resolve import resolve_doi
import json, warnings


warnings.filterwarnings('ignore')
def get_mate_item(bs, attrs_value='dc.title'):
    # Find the meta tag with name "dc.title"
    meta_tag = bs.find('meta', attrs={'name': attrs_value})
    # Extract the content attribute
    item_content = ""
    if meta_tag and 'content' in meta_tag.attrs:
        item_content = meta_tag['content']            

    return item_content


class Reference(StructuredNode):
    nodeid = StringProperty(unique_index=True, required=True)
    title = StringProperty(required=True)
    type = StringProperty()     # Journal, Conference, Thesis, Report, etc
    authors = ArrayProperty(required=True, base_property=StringProperty())
    affiliations = ArrayProperty(required=True, base_property=StringProperty())
    doi = StringProperty()
    url = StringProperty()           # URL of the source
    published_name = StringProperty()   # Journal/Conference name
    published_date = DateTimeProperty()   # Date of publication


# Extract bibtex information from the HTML file, using https://github.com/timothygebhard/doi2bibtex
def get_bib_doi(bs, store_dir, cls_name='Reference', contain_affiliation=False):
    # Extract the publisher information
    if contain_affiliation:
        pulisher = bs.find('meta', attrs={'property': 'og:site_name'})
        author_affiliations = []
        if pulisher['content'] in ['Wiley Online Library', 'Nature']:
            meta_tags = ['citation_author', 'citation_author_institution']        
            meta_authors = bs.find_all('meta', attrs={'name': meta_tags[0]})
            meta_affiliations = bs.find_all('meta', attrs={'name': meta_tags[1]})
            # Iterate through each meta tag and print the content
            for index, meta_author_tag in enumerate(meta_authors):
                print(f"Meta tag {index} content: {meta_author_tag['content']}")
                author_affiliations.append({meta_author_tag['content']: meta_affiliations[index]['content']})
        elif pulisher['content'] in ["ACS Publications"]:
            meta_tags = ['og:title', "og:type", 'og:url', "publication_doi"]
        else:
            meta_tags = ['og:title', "og:type", 'og:url', 'publication_doi']

        print("=========", author_affiliations)

    paper_title = bs.find('meta', attrs={'property': 'og:title'})['content']    
    paper_title = re.sub(r'/', '', paper_title)

    # Get DOI from the meta tags in the HTML file
    meta_doi_tags = ["dc.identifier", "publication_doi", "citation_doi", "prism.doi"]
    for meta_tag in meta_doi_tags:
        meta_doi = bs.find('meta', attrs={'name': meta_tag})
        if meta_doi is not None: 
            meta_doi = meta_doi['content']
            break    
    
    # Resolve the DOI to get the bibtex information    
    doi_pattern = r'^10\.\d{4,9}/[-._;()/:A-Z0-9]+$'
    meta_doi = re.sub(r'doi:', '', meta_doi)  # Remove any slashes in the DOI as Nature articles have slashes in the DOI
    if re.match(doi_pattern, meta_doi, re.IGNORECASE) is not None:  # Check if the DOI is valid
        bib_info = resolve_doi(meta_doi) 

    # Extract the reference attribute
    properties = {}  # Extract key information
    node_reference = globals()[cls_name]
    for att_array in node_reference.__all_properties__: 
        attr = att_array[0]
        if attr == "type":
            properties[attr] = bib_info.get('ENTRYTYPE')
        elif attr == "authors":
            # Split the string on " and "
            authors_list = bib_info.get('author').split(" and ")
            # Clean up each part and format the output
            properties[attr] = [author.replace(',', '').strip() for author in authors_list]
            print(properties[attr])
        elif attr == "affiliations":
            properties[attr] = bib_info.get('citation_author_institution')
        elif attr == "published_name":
            properties[attr] = bib_info.get('journal')
        elif attr == "doi":               
            properties[attr] = meta_doi
        elif attr == "published_date":
            properties[attr] = bib_info.get('year')
        elif attr == "title":
            properties[attr] = paper_title
        else:
            properties[attr] = bib_info.get(attr)

    # print(properties)    
    json_bib = {node_reference.__name__: {"properties": properties,}}    # Create the JSON template 
    json_bibcontent = json.dumps(json_bib, indent=4, ensure_ascii=False)
    # print(json_bibcontent)
    # Write to a JSON file
    json_name = re.sub(r'/', '_', meta_doi)
    bib2json_path = join(store_dir, json_name + ".json")
    with open(bib2json_path, 'w', encoding='utf-8') as json_file:
        json_file.write(json_bibcontent)    

    return "DOI: " + meta_doi, paper_title


# Extract the content of the articles published in the journal "Advanced Energy Materials", 'Advanced Materials'
def extract_artical(html_file_path, store_dir):
    # Read the HTML file
    with open(html_file_path, "r") as file:
        html = file.read()
    # Use Beautidulsoup to extract information from html
    bs = BeautifulSoup(html, 'html.parser')
    print("Extracting data from", html_file_path)

    artical_doi, artical_title = get_bib_doi(bs, store_dir)

# Extract description
    pulisher = bs.find('meta', attrs={'property': 'og:site_name'})['content']    
    if pulisher in ['Wiley Online Library']:
        desc_arr = bs.find_all('section', class_=['article-section__content'])
    elif pulisher in ['Science']:
        desc_arr = bs.find_all('div', attrs={'class': 'core-container'})
        # desc_arr = bs.find_all('div', attrs={'role': 'paragraph'})
    elif pulisher in ["Nature"]:   
        desc_arr = bs.find_all('div', class_=['main-content'])   #Nature        
    elif pulisher in ["ACS Publications"]:
        desc_arr = bs.find_all('div', class_=['article_content-left'])
    else:
        desc_arr = []
        print("No content class found for the artical titled", artical_title)
   
    artical_date = artical_doi        
    for desc in desc_arr:
        # Remove all <img> tags and their content
        remove_tags = ['img', 'figure','ol','button','span']
        for rm_tag in remove_tags:
            for dese_tag in desc.find_all(rm_tag): 
                if rm_tag in ['img', 'ol','button']:
                    dese_tag.replace_with(' ')
                elif rm_tag in ['span']:
                    if dese_tag.find('a') is not None:  #Wiley
                        dese_tag.extract()
                    span_tagcls = dese_tag.get('class')
                    if span_tagcls is not None:
                        if span_tagcls[0] in ['mathjax-tex']:  # Nature
                            dese_tag.extract()  # Removes the <span> tag along with its contents
                else:
                    dese_tag.extract()
                    # pass                

        # Find the div with the specific class and remove its contents
        remove_divs = ['loa-wrapper loa-authors hidden-xs desktop-authors', 'c-article-section__figure-description', 'authorInformationSection', 'article__copy', 'ack', 'c-article-equation', 'c-article-equation__content']
        for rm_div in remove_divs:
            for dese_div in desc.find_all('div', class_=rm_div):         
                dese_div.replace_with(" ")

        remove_elements = ['figure'] # Remove the <figure> element
        for rm_elem in remove_elements:
            for dese_elem in desc.find_all(rm_elem):
                dese_elem.extract()

        for div_pra in desc.find_all('div', class_=['NLM_p']):
            div_pra.insert_before(bs.new_tag('br'))
            # tmp = bs.new_tag('p')
            # tmp.append(div_pra)
            # div_pra = tmp            

        extract_tags =  ['sub', 'i', 'sup']
        for ext_tag in extract_tags:
            for a_tag in desc.find_all(ext_tag): 
                if ext_tag is 'sup' and (a_tag.get_text() in ['[',']'] or a_tag.find('a') is not None):
                    a_tag.extract()
                else:
                    a_tag.replace_with(a_tag.text)

        for a_tag in desc.find_all('a'):            
            if a_tag.get('class') is not None:
                # print("===***===",a_tag.get('class'))
                if a_tag.get('class')[0] in ['open-in-viewer', 'suppLink', 'ext-link', 'internalNav']:                    
                    a_tag.replace_with(a_tag.text)  # Replace the <a> tag with its text content
                elif a_tag.get('class')[0] in ['ref', 'bibLink', 'article__tags__link', 'open-figure-link', 'ppt-figure-link']:  # Remove ACS references
                    a_tag.extract()
                else:                       
                    a_tag.replace_with(" ") 
            else:
                if a_tag.get('role') in ["doc-biblioref"] or a_tag.get('href').find("https://onlinelibrary.wiley.com") != -1 or a_tag.get('href').find("https://www.nature.com/") != -1:
                    a_tag.replace_with(a_tag.text)
                else:
                    a_tag.replace_with(" ")

        # desc_str_no_spaces = re.sub(r'\[.*?\]', ' ', desc_str_no_spaces)  # Remove []  
        # desc_str_no_spaces = re.sub(r'\(\)', ' ', desc_str_no_spaces)  # Remove () 

        artical_date = artical_date + '\n' + str(desc).strip()

# (1) html2Markdown
    # Create a new BeautifulSoup object from the modified HTML content
    extract_html = BeautifulSoup(artical_date, 'html.parser')
    mdfile = join(store_dir, artical_title + ".md")
    with open(mdfile, "w") as file:
        # markdown_content = md(desc, strong_em_symbol="", escape_misc=False)  # Convert HTML to markdown
        markdown_content = MarkdownConverter(strip=['img', 'figure', 'ol'], strong_em_symbol="", escape_misc=False).convert_soup(extract_html)
        markdown_content = re.sub(r'\n', '\n\n', str(markdown_content))
        markdown_content = re.sub(r'\n\s*\n', '\n\n', str(markdown_content))   # Merge consecutive empty lines into a single empty line
        file.write(str(markdown_content))

# (2) html2text
    with open("tmp.html", "w") as file:
        file.write(artical_date)

#   strip_markdown.strip_markdown_file(store_dir)  # Converts markdown to plain text
    textfile = join(store_dir, artical_title + ".txt")    
    with open(textfile, "w") as file:
        file.write(str(markdown_content))


if __name__ == "__main__": 
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # Directory to search
    jounal_name = ['wiley Advanced Energy Materials', 'wiley Advanced Materials', 'wiley Small', 'Nature Energy', 'Nature Communications']
    # jounal_name = ['Science', 'ACS Energy Letters', 'ACS Nano', 'ACS Nano Letters'] 
    dir_path = join(current_dir, 'sulfideSSE', jounal_name[0]) 
    html_files = glob.glob(join(dir_path, '*.html'), recursive=True)

# Use glob to find all .html files
    dir_path = join(current_dir, 'sulfideSSE')     
    html_files = glob.glob(join(dir_path, '*', '*.html'), recursive=True)    

    # Print the paths of all .html files
    for html_file in html_files:
        if os.path.isfile(html_file):
            extract_artical(html_file, join(current_dir, 'rstdir'))

