from shutil import rmtree
from os import walk, mkdir, environ
from os.path import splitext, join, exists
from absl import flags, app
from tqdm import tqdm
from langchain.document_loaders import UnstructuredMarkdownLoader
import torch
from torch import device
from huggingface_hub import login
from transformers import AutoTokenizer, AutoModelForCausalLM, LogitsProcessorList, TemperatureLogitsWarper, TopPLogitsWarper
from langchain.llms.base import LLM
from langchain_core.prompts.prompt import PromptTemplate

def Llama3(locally = False):
  assert locally == True, "must be locally!"
  class LLama3FA2(LLM):
    tokenizer: AutoTokenizer = None
    model: AutoModelForCausalLM = None
    def __init__(self,):
      super().__init__()
      self.tokenizer = AutoTokenizer.from_pretrained('meta-llama/Meta-Llama-3.1-8B-Instruct', trust_remote_code = True)
      self.tokenizer.pad_token_id = 128001
      self.model = AutoModelForCausalLM.from_pretrained('meta-llama/Meta-Llama-3.1-8B-Instruct', attn_implementation = 'flash_attention_2', torch_dtype = torch.float16, trust_remote_code = True)
      self.model = self.model.to(device('cuda'))
      self.model.eval()
    def _call(self, prompt, stop = None, run_manager = None, **kwargs):
      logits_processor = LogitsProcessorList()
      logits_processor.append(TemperatureLogitsWarper(0.6))
      logits_processor.append(TopPLogitsWarper(0.9))
      inputs = self.tokenizer(prompt, return_tensors = 'pt')
      inputs = inputs.to(device('cuda'))
      outputs = self.model.generate(**inputs, logits_processor = logits_processor, use_cache = True, do_sample = True, max_length = 131072)
      outputs = outputs.tolist()[0][len(inputs["input_ids"][0]):-1]
      response = self.tokenizer.decode(outputs)
      return response
    @property
    def _llm_type(self):
      return "llama3.1 with flast attention 2"
  llm = LLama3FA2()

  return llm.tokenizer, llm


def Qwen2(locally = False):
  assert locally == True, "must be locally!"
  class Qwen2FA2(LLM):
    tokenizer: AutoTokenizer = None
    model: AutoModelForCausalLM = None
    def __init__(self,):
      super().__init__()
      self.tokenizer = AutoTokenizer.from_pretrained('Qwen/Qwen2.5-7B-Instruct', trust_remote_code = True)
      self.model = AutoModelForCausalLM.from_pretrained('Qwen/Qwen2.5-7B-Instruct', attn_implementation = 'flash_attention_2', torch_dtype = torch.float16, trust_remote_code = True)
      self.model = self.model.to(device('cuda'))
      self.model.eval()
    def _call(self, prompt, stop = None, run_manager = None, **kwargs):
      logits_processor = LogitsProcessorList()
      logits_processor.append(TemperatureLogitsWarper(0.8))
      logits_processor.append(TopPLogitsWarper(0.8))
      inputs = self.tokenizer(prompt, return_tensors = 'pt')
      inputs = inputs.to(device('cuda'))
      outputs = self.model.generate(**inputs, logits_processor = logits_processor, use_cache = True, do_sample = True, max_length = 131072)
      outputs = outputs.tolist()[0][len(inputs["input_ids"][0]):-1]
      response = self.tokenizer.decode(outputs)
      return response
    @property
    def _llm_type(self):
      return "qwen2 with flast attention 2"
  llm = Qwen2FA2()

  return llm.tokenizer, llm


def experimental_template(tokenizer):
  messages = [
    {'role': 'system', 'content': 'Given a full text of a paper. Please return the original text of the experimental part of the paper. If the experimental part is not present in the paper, just return "<no experimental>".'},
    {'role': 'user', 'content': 'the full text:\n\n{text}'}
  ]
  prompt = tokenizer.apply_chat_template(messages, tokenize = False, add_generating_prompt = True)
  template = PromptTemplate(template = prompt, input_variables = ['text'])
  return template


def experimental_chain(llm, tokenizer):
  exp_tmp = experimental_template(tokenizer)
  exp_chain = exp_tmp | llm
  return exp_chain



FLAGS = flags.FLAGS

def add_options():
  flags.DEFINE_string('input_dir', default = 'pre_text', help = 'path to input directory')
  flags.DEFINE_string('output_dir', default = 'processed', help = 'path to output directory')
  flags.DEFINE_enum('model', default = 'qwen2', enum_values = {'llama3', 'qwen2'}, help = 'model to use')

def main(unused_argv):
  if exists(FLAGS.output_dir): rmtree(FLAGS.output_dir)
  mkdir(FLAGS.output_dir)
  tokenizer, llm = {
    'llama3': Llama3,
    'qwen2': Qwen2}[FLAGS.model](True)
  exp_chain = experimental_chain(llm, tokenizer)
  for root, dirs, files in tqdm(walk(FLAGS.input_dir)):
    for f in files:
      stem, ext = splitext(f)
      if ext != '.txt': continue
      loader = UnstructuredMarkdownLoader(join(root, f), model = 'single', strategy = 'fast')
      text = ' '.join([doc.page_content for doc in loader.load()])
      results = exp_chain.invoke({'text': text})
      with open(join(FLAGS.output_dir, stem + '.txt'), 'w') as f:
        f.write(results)

if __name__ == "__main__":
  add_options()
  app.run(main)