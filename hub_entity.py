
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


# Chemistry Entity such as Electrolyte, Precursor, Catalyst
class ChemNode(StructuredNode):
     nodeid = StringProperty(unique_index=True, required=True)  # The unique identifier of the entity
     name = StringProperty(required=True)
     alias = ArrayProperty(base_property=StringProperty())
     chem_formula = StringProperty(help_text="The chemical formula of the entity.")


# Experiment Node such as device, operations, etc
class BaseNode(StructuredNode):
     nodeid = StringProperty(unique_index=True, required=True)
     name = StringProperty(required=True)
     alias = ArrayProperty(base_property=StringProperty())


class Battery(BaseNode): 
    subcategory = StringProperty(help_text="The subcategory of this type of battery.")
    feature = StringProperty(help_text="The detailed feature of this type of battery.")
    electrolyte = RelationshipFrom("Electrolyte", "Make_by")


class Electrolyte(ChemNode): 
     subcategory = StringProperty()
     feature = StringProperty()     
     
     volum_energy_density = FloatProperty(help_text="The unit is Wh/kg.")  # The unit of volumetric energy density is Wh/kg
     gravi_energy_density = FloatProperty(help_text="The unit is Wh/kg.")  # The unit of gravimetric energy density is Wh/kg
     young_modulus = FloatProperty(help_text="The unit is GPa.")   # The unit is GPa, 1MPa = 0.001GPa
     echem_stablity_window = FloatProperty(help_text="The unit is V.")  # The unit is V
     
     precursor = RelationshipTo("Precursor", "Need")
     synthesis_operation = RelationshipTo("SynthesisOperation", "Synthesis_with")
     Conductivity = RelationshipTo("Conductivity", "Own")     # Define outgoing relationships. This indicates that the current node has a relationship pointing to another node.
     reference = RelationshipTo("Reference", "Presented_BY")
     battery = RelationshipTo("Battery", "Use_for")
     

class Precursor(ChemNode):
     chem_function = StringProperty()

     catalyst = RelationshipFrom("Catalyst", "React_with")
     electrolyte = RelationshipFrom("Electrolyte", "Need_BY")


class Catalyst(ChemNode):
     chem_function = StringProperty() 

     precursor = RelationshipTo("Precursor", "React_for")
     reference = RelationshipTo("Reference", "Presented_BY")


class Conductivity(StructuredNode):
     entid = StringProperty(unique_index=True, required=True)
     value = FloatProperty(required=True, help_text="The unit is Siemens per meter (S/m)")
     temperature = FloatProperty(help_text="The unit is centigrade (°C). The temperature at which the conductivity was measured")

     electrolyte = RelationshipTo("Electrolyte", "Own_BY")


class CrystalStructure(StructuredNode):
    nodeid = StringProperty(unique_index=True, required=True)
    name = StringProperty(required=True)
    crystal_family = StringProperty()
    crystal_system = StringProperty()
    crystal_class = StringProperty()
    point_sysmetry = StringProperty()

    space_group = RelationshipTo("SpaceGroup", "Belong")


# There are 230 distinct space groups, which are classified into 7 crystal systems, 14 Bravais lattices, and 32 crystal classes.
class SpaceGroup(StructuredNode):
    nodeid = StringProperty(unique_index=True, required=True)
    name = StringProperty(required=True)
    sg_dimension = IntegerProperty(default=2)

    crystal_structure = RelationshipFrom("CrystalStructure", "Belong_to")
    

class ReactionDevice(BaseNode): 
    function = StringProperty(help_text="The detailed function of this device.")


# Reaction Condition such as Temperature, Pressure, etc
class ReactionCondition(BaseNode):  
    rule = StringProperty(help_text="The detailed description of this condition.") 
    temperature = ArrayProperty(base_property=FloatProperty(), help_text="[23.6] or [23.6, 58.9]. Its unit is centigrade (°C).")
    reaction_time = StringProperty(help_text="Unit is hour(h), minute(min), second(s), millisecond(ms), etc.")
    

# Synthesis Operation such as Mixing, Heating, etc
class SynthesisOperation(BaseNode):  
     operation_detail = StringProperty(help_text="The detailed description of this operation.")

     precursor = RelationshipTo("Precursor", "Operation_used")
     reaction_condition = RelationshipTo("ReactionCondition", "Perform_with")
     reaction_device = RelationshipTo("ReactionDevice", "Operate_with")
     next_operation = RelationshipTo("SynthesisOperation", "Next") 
     electrolyte = RelationshipFrom("Electrolyte", "Synthesis_target") 
    

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
    


# Export the node definitions to a JSON file for collecting its properties and relationships, without sorting alphabetically
def generate_json_template(node_class):
     properties = {}
     relationships = {}

     for att_array in node_class.__all_properties__:          
     # for attr in dir(node_class): # Properties and relationships are sorted alphabetically
          # if not attr.startswith('_'):     # Skip private attributes and methods
               # property_obj = getattr(node_class, attr)  # Get the attribute's type
          attr = att_array[0]
          property_obj = getattr(node_class, attr)
          if isinstance(property_obj, StringProperty):
               properties[attr] = "String"
          elif isinstance(property_obj, IntegerProperty):
               properties[attr] = "Integer"
          elif isinstance(property_obj, FloatProperty):
               properties[attr] = "Float-point value"
          elif isinstance(property_obj, ArrayProperty):
               properties[attr] = "['string1', 'string2']"
          elif isinstance(property_obj, DateTimeProperty):
               properties[attr] = "A datatime string such as '2023-10-04 00:00:00'"

     for att_array in node_class.__all_relationships__: 
          attr = att_array[0] 
          property_obj = getattr(node_class, attr)    
          # Check for relationships
          if isinstance(property_obj, RelationshipTo):
               relationships[attr] = "related_to: A array of json files"  # The related node class 
          elif isinstance(property_obj, RelationshipFrom):
               relationships[attr] = "related_form: A array of json files"


     # Create the JSON template
     json_template = {
          node_class.__name__: {
               # "label": node_class.__label__,
               "properties": properties,
               "relationships": relationships
          }
     }

     # Convert to JSON
     return json.dumps(json_template, indent=4, ensure_ascii=False)


def export_json_template(save_path):
     if not os.path.exists(save_path):
          os.makedirs(save_path)
     # BTY-Battery, ELT-Electrolyte, PRC-Precursor, CTY-Catalyst, CDT-Conductivity, CYS-CrystalStructure, SGP-SpaceGroup
     # RTD-ReactionDevice, RTC-ReactionCondition, SOP-SynthesisOperation, REF-Reference
     node_clsname = ["Battery", "Electrolyte", "Precursor", "Catalyst", "Conductivity", "CrystalStructure", "SpaceGroup", "ReactionDevice", "ReactionCondition", "SynthesisOperation", "Reference"]
     
     for clsname in node_clsname:
          node_class = globals()[clsname]
          # Generate and print the JSON template for the Person class
          json_template = generate_json_template(node_class)
          print(json_template)
          # Write to a JSON file
          with open(os.path.join(save_path, f'{clsname}_template.json'), 'w', encoding='utf-8') as json_file:
               json_file.write(json_template)


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
def init_node2(json_file):
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
     

# TODO: Generate the vector of properties and relationships of a node
def generate_vector(node_class):
     properties = []
     relationships = []

     for att_array in node_class.__all_properties__:          
          attr = att_array[0]
          properties.append(attr)

     for att_array in node_class.__all_relationships__: 
          attr = att_array[0] 
          relationships.append(attr)

     return properties, relationships


# Update the relationships of a node using a JSON data
def update_relationships(json_file):
     pr_data = load_json_data(json_file)
                       
     try:
          for cls_key in pr_data.keys():          
               node_class = globals()[cls_key]
               pr_value = pr_data[cls_key]
               for pr_key in pr_value.keys():
                    if pr_key == "relationships":
                         for rel_key in pr_value[pr_key].keys():
                              relation_value = pr_value[pr_key][rel_key]
                              ents_relation = eval('node_class.%s' % rel_key)
                              if isinstance(ents_relation, RelationshipTo):
                                   ents_relation = RelationshipTo("RelatedNode", "related_to")
                              elif isinstance(ents_relation, RelationshipFrom):
                                   ents_relation = RelationshipFrom("RelatedNode", "related_form")
     except Exception as e:
          print(e)
     
     node_class.save()


if __name__ == '__main__':
     save_dir='json_template'
     save_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), save_dir)
     # export_json_template(save_path)

     setup_neo4j('neo4j')
     save_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'mdtext')
     json_file = os.path.join(save_path, '10.1002_smll.202306763.json')
     init_node(json_file)
