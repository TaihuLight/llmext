
from neomodel import StructuredNode, FloatProperty, IntegerProperty, DateTimeProperty, StringProperty, ArrayProperty, RelationshipTo, RelationshipFrom, config
import json, os, ast
from datetime import datetime

"""
Rules:
- The property "nodeid" is in the format of [Uppercase of the abbreviation of class name]-[developer_name(lifd)]-[date(20241017)]-[index(3 numbers)], where the abbreviation of class name is shown as the comment of the class,
  deveper_name is the abbreviation of the developer's name such as lifd coming from lifada.
- Multiple instances of the same entity have different nodeid, but stored in a same JSON file.
- null is used to indicate that a property is not avaiable.
"""

def setup_neo4j(database_name = 'neo4j'):
     config.DATABASE_URL = 'bolt://neo4j:19841124@103.6.49.76:7687'
     config.DATABASE_NAME = database_name
     config.FORCE_TIMEZONE = True

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
    

# Load the JSON data from a file
def load_json_data(json_file):
     with open(json_file) as pr_file:          
          try:
               pr_data = json.load(pr_file)
          except Exception as e:
               print(e)
     return pr_data


def determine_datetime_format(prop_value):
     formats = [('%Y-%m-%d %H:%M:%S', lambda val: len(val) == 19 and val.count('-') == 2 and val.count(':') == 2),
        ('%Y-%m-%d', lambda val: len(val) == 10 and val.count('-') == 2),
        ('%Y', lambda val: len(val) == 4)]

     for format_str, condition in formats:
        if condition(prop_value):
            return format_str

     return None


# Initialize a node with its properties and relationships using a JSON data
def init_node(json_file):
     pr_data = load_json_data(json_file)

     try:
          for cls_key in pr_data.keys():          
               node_class = globals()[cls_key]()
               pr_value = pr_data[cls_key]
               for pr_key in pr_value.keys():
                    if pr_key == "properties":
                         for prop_key in pr_value[pr_key].keys():
                              prop_value = pr_value[pr_key][prop_key]
                              print(prop_key, prop_value)
                              ent_property = eval('node_class.%s' % prop_key)
                              if isinstance(ent_property, StringProperty):
                                   ent_property = prop_value
                              elif isinstance(ent_property, IntegerProperty):
                                   ent_property = int(prop_value)
                              elif isinstance(ent_property, FloatProperty):
                                   ent_property = float(prop_value)
                              elif isinstance(ent_property, ArrayProperty):
                                   ent_property = prop_value
                              elif isinstance(ent_property, DateTimeProperty):
                                   datetime_format = determine_datetime_format(prop_value)
                                   if datetime_format:
                                        ent_property = datetime.strptime(prop_value, datetime_format)
                                   else:
                                        ent_property = "None"
                              else:
                                   ent_property = "None"
               node_class.save()    
     except Exception as e:
          print(e)
     

if __name__ == '__main__':
     setup_neo4j('neo4j')
     save_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'mdtext')
     json_file = os.path.join(save_path, '10.1002_smll.202306763.json')
     init_node(json_file)
