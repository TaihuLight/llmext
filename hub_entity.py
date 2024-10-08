
from neomodel import StructuredNode, FloatProperty, IntegerProperty, DateTimeProperty, StringProperty, ArrayProperty, RelationshipTo, RelationshipFrom, config


def setup_neo4j(database_name = 'neo4j'):
     config.DATABASE_URL = 'bolt://neo4j:19841124@103.6.49.76:7687'
     config.DATABASE_NAME = database_name
     config.FORCE_TIMEZONE = True


# Chemistry Entity such as Electrolyte, Precursor, Catelyst
class ChemNode(StructuredNode):
     uid = StringProperty(unique_index=True, required=True)
     name = StringProperty(required=True)
     alias = ArrayProperty(base_property=StringProperty())
     chem_formula = StringProperty()


# Experiment Node such as device, operations, etc
class ExperimentNode(StructuredNode):
     uid = StringProperty(unique_index=True, required=True)
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
     uid = StringProperty(unique_index=True, required=True)
     value = FloatProperty(required=True, help_text="The unit is Siemens per meter (S/m)")
     temperature = FloatProperty(help_text="The unit is centigrade (°C). The temperature at which the conductivity was measured")

     electrolyte = RelationshipTo("Electrolyte", "Owned_BY")


class CrystalStructure(StructuredNode):
    uid = StringProperty(unique_index=True, required=True)
    name = StringProperty(required=True)
    crystal_family = StringProperty()
    crystal_system = StringProperty()
    crystal_class = StringProperty()
    point_sysmetry = StringProperty()

    space_group = RelationshipTo("SpaceGroup", "Belong")


# There are 230 distinct space groups, which are classified into 7 crystal systems, 14 Bravais lattices, and 32 crystal classes.
class SpaceGroup(StructuredNode):
    uid = StringProperty(unique_index=True, required=True)
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
    uid = StringProperty(unique_index=True, required=True)
    title = StringProperty(required=True)
    type = StringProperty()     # Journal, Conference, Thesis, Report, etc
    authors = ArrayProperty(required=True, base_property=StringProperty())
    affiliations = ArrayProperty(required=True, base_property=StringProperty())
    doi = StringProperty()
    url = StringProperty()           # URL of the source
    published_name = StringProperty()   # Journal/Conference name
    published_date = DateTimeProperty()   # Date of publication
    