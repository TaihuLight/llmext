
from neomodel import StructuredNode, FloatProperty, IntegerProperty, DateTimeProperty, StringProperty, ArrayProperty, RelationshipTo, RelationshipFrom, config
import json, os

def setup_neo4j(database_name = 'neo4j'):
     config.DATABASE_URL = 'bolt://neo4j:19841124@103.6.49.76:7687'
     config.DATABASE_NAME = database_name
     config.FORCE_TIMEZONE = True


# Chemistry Entity such as Electrolyte, Precursor, Catelyst
class ChemNode(StructuredNode):
     nodeid = StringProperty(unique_index=True, required=True)
     name = StringProperty(required=True)
     alias = ArrayProperty(base_property=StringProperty())
     chem_formula = StringProperty(help_text="The chemical formula of the entity.")


# Experiment Node such as device, operations, etc
class ExperimentNode(StructuredNode):
     nodeid = StringProperty(unique_index=True, required=True)
     name = StringProperty(required=True)
     alias = ArrayProperty(base_property=StringProperty())
     

class Electrolyte(ChemNode): 
     subcategory = StringProperty()
     feature = StringProperty()     
     
     volum_energy_density = FloatProperty()  # The unit of volumetric energy density is Wh/kg
     gravi_energy_density = FloatProperty()  # The unit of gravimetric energy density is Wh/kg
     young_modulus = FloatProperty()   # The unit is GPa, 1MPa = 0.001GPa
     echem_stablity_window = FloatProperty()  # The unit is V
     synthesis_steps = ArrayProperty(base_property=StringProperty(), help_text="The operation uids to synthesize the electrolyte.")
     
     precursor = RelationshipTo("Precursor", "Needed")
     systhesis_operation = RelationshipTo("SynthesisOperation", "Systhesis_with")
     conductiviy = RelationshipTo("Conductiviy", "Owned")     # Define outgoing relationships. This indicates that the current node has a relationship pointing to another node.
     reference = RelationshipTo("Reference", "Presented_BY")
     

class Precursor(ChemNode):
     function = StringProperty()

     electrolyte = RelationshipFrom("Electrolyte", "Needed_BY")


class Catelyst(ChemNode):
     chem_function = StringProperty() 

     reference = RelationshipTo("Reference", "Presented_BY")


class Conductiviy(StructuredNode):
     entid = StringProperty(unique_index=True, required=True)
     value = FloatProperty(required=True, help_text="The unit is Siemens per meter (S/m)")
     temperature = FloatProperty(help_text="The unit is centigrade (°C). The temperature at which the conductivity was measured")

     electrolyte = RelationshipTo("Electrolyte", "Owned_BY")


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
    

class ReactionDevice(ExperimentNode): 
    function = StringProperty(help_text="The detailed function of this device.")


# Reaction Condition such as Temperature, Pressure, etc
class ReactionCondition(ExperimentNode):  
    rule = StringProperty(help_text="The detailed description of this condition.") 
    temperature = FloatProperty(help_text="The unit is centigrade (°C).")
    reaction_time = StringProperty(help_text="Unit is hour(h), minute(min), second(s), millisecond(ms), etc.")
    

# Synthesis Operation such as Mixing, Heating, etc
class SynthesisOperation(ExperimentNode):  
     operation_detail = StringProperty(help_text="The detailed description of this operation.")

     precursor = RelationshipTo("Precursor", "Operation_used")
     reaction_condition = RelationshipTo("ReactionCondition", "Performed_with")
     reaction_device = RelationshipTo("ReactionDevice", "Performed_with")
     next_operation = RelationshipTo("SynthesisOperation", "Next") 
     electrolyte = RelationshipFrom("Electrolyte", "Systhesis_target") 
    

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
               properties[attr] = "Array of strings such as ['string1', 'string2']"
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
               "label": node_class.__label__,
               "properties": properties,
               "relationships": relationships
          }
     }

     # Convert to JSON
     return json.dumps(json_template, indent=4, ensure_ascii=False)


if __name__ == '__main__':
     node_clsname = ["Electrolyte", "Precursor", "Catelyst", "Conductiviy", "CrystalStructure", "SpaceGroup", "ReactionDevice", "ReactionCondition", "SynthesisOperation", "Reference"]
     dir_path = os.path.dirname(os.path.realpath(__file__))
     save_path = os.path.join(dir_path, 'json_template')
     if not os.path.exists(save_path):
          os.makedirs(save_path)
          
     for clsname in node_clsname:
          node_class = globals()[clsname]
          # Generate and print the JSON template for the Person class
          json_template = generate_json_template(node_class)
          print(json_template)
          # Write to a file
          with open(os.path.join(save_path, f'{clsname}_template.json'), 'w', encoding='utf-8') as json_file:
               json_file.write(json_template)


