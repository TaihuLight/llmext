from typing import List, Dict
from langchain_core.pydantic_v1 import BaseModel, Field, create_model
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts.prompt import PromptTemplate



def extract_electrolyte_langchain(tokenizer):
  class Electrolyte(BaseModel):
    electrolyte: Dict[str, str] = Field(description = "a dictionary representing an electrolyte whose keys are elements' chemical formulas and values are their proportions in float format.")
  parser = JsonOutputParser(pydantic_object = Electrolyte)
  instructions = parser.get_format_instructions()
  system_message = """Given a full text of a patent about how an electrolyte is synthesised. Extract the elements and their proportions of the electrolyte synthesised in the first example.
""" + \
instructions + \
"""
The following are several examples of how an electrolyte target is extracted from a context.

Example 1
Input context:
---------------------
The resultant powdery sulfide-based solid electrolyte was analyzed through powdery X-ray diffraction (XRD) using an X-ray diffractometer (XRD) (Smart Lab Apparatus, manufactured by Rigaku Corporation). Any other peak than the peaks derived from the raw materials was not detected. Analyzed using an ICP emission spectrometric apparatus, the composition was Li:S:P:Br:I (by mol)=1.390:1.590:0.400:0.109:0.101.
---------------------
Output electrolyte:
{"Li":1.390,"S":1.590,"P":0.400,"Br":0.109,"I":0.101}

Example 2
Input context:
---------------------
The sulfide solid electrolyte was subjected to an ICP analysis, and the molar ratio of each element was measured. The ionic conductivity and the residual ratio were measured. The results are shown in Table 1.
	TABLE 1
	
	Molar ratio of each 		
	element to phosphorus 		Ionic conductivity
	a 	b 	c 			(σ)
	(Li/P) 	(S/P) 	(Cl/P) 	a − b 	a + c 	(mS/cm)
	
Ex. 1 	5.40 	4.45 	1.70 	0.95 	7.10 	8.9
---------------------
Output electrolyte:
{"Li":5.40,"S":4.45,"Cl":1.70,"P":1.00}



Example 3:
Input context:
---------------------
(S3) The amorphized powder mixture was crystallized through thermal treatment at a temperature of about 500° C. for 4 hr, thereby yielding a solid electrolyte having an argyrodite-type crystal structure, as represented by Chemical Formula 2 below.
Li6PS5Cl [Chemical Formula 2] 
---------------------
Output electrolyte:
{"Li":6.00,"P":1.00,"S":5.00,"Cl":1.00}
"""
  system_message = system_message.replace('{','{{')
  system_message = system_message.replace('}','}}')
  messages = [
    {"role": "system", "content": system_message},
    {"role": "user", "content": "{patent}"}
  ]
  prompt = tokenizer.apply_chat_template(messages, tokenize = False, add_generation_prompt = True)
  template = PromptTemplate(template = prompt, input_variables = ['patent'])
  return template, parser