from llama_index.llms.openai_like import OpenAILike
from llama_index.llms.huggingface import HuggingFaceLLM
from llama_index.llms.dashscope import DashScope, DashScopeGenerationModels
from llama_index.embeddings.huggingface import HuggingFaceEmbedding

import os
from huggingface_hub import login

# Change the default cache dir for "/tmp/llama_index"
os.environ["LLAMA_INDEX_CACHE_DIR"]  = "/home/xieyi/raid/llama_index"
# To configure where huggingface_hub will locally store data. In particular, your token and the cache will be stored in this folder.
os.environ["HF_HOME"] = "/home/xieyi/raid/huggingface"
# API access to llama-cloud
os.environ["LLAMA_CLOUD_API_KEY"] = "llx-FTCVt2lKH0tBAHPyj0QjJxPMi42BDvoE3LK3jJP1ii5qsRdr"
token_huggingface = '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'
LLM_DEVICE = "cuda:1"


def embed_model(model_name = "BAAI/bge-large-en-v1.5"):
    # from llama_index.embeddings.openai import OpenAIEmbedding
    # embed_model = OpenAIEmbedding(model="text-embedding-3-large")
    embed_model = HuggingFaceEmbedding(model_name=model_name, device=LLM_DEVICE)
    return embed_model


def Qwen():
    return DashScope(model_name=DashScopeGenerationModels.QWEN_TURBO, api_key="sk-a24c579290f74665a3653bfdc5050098")

def Qwen2():
    QWEN_API_KEY = "sk-a24c579290f74665a3653bfdc5050098"
    # API_KEY = "37cd3e06d9754653910c7bce12ff5d61"
    # llm = OpenAILike(api_base="https://api.01.ai/v1", api_key=API_KEY, model="yi-large",  is_chat_model=True)

    llm = OpenAILike(api_base="https://dashscope.aliyuncs.com/compatible-mode/v1", api_key=QWEN_API_KEY, model="qwen2-72b-instruct",  is_chat_model=True)
    return llm


def llm_hgface_llamaindex(llm_name = "Qwen/Qwen2-72B-Instruct"):
    #  login(token = token_huggingface)
     llm_model = HuggingFaceLLM(
          model_name=llm_name,
          tokenizer_name=llm_name,
          context_window=3900,
          max_new_tokens=256,
          # model_kwargs={"quantization_config": quantization_config},
          generate_kwargs={"do_sample": False, "temperature": 0.8, "top_k": 10},
          # messages_to_prompt=messages_to_prompt,
          # completion_to_prompt=completion_to_prompt,
          device_map=LLM_DEVICE,
     )
     return llm_model


def Yi(model_name = "yi-large"):
    # Using 01.AI API for embeddings/llms
    YIAI_KEY = "37cd3e06d9754653910c7bce12ff5d61"
    return OpenAILike(api_base="https://api.01.ai/v1", api_key=YIAI_KEY, model=model_name, is_chat_model=True, do_sample=False, temperature=0.0)


def OpenAI_GPT(model_name = "gpt-4o-mini-2024-07-18"):    
    from llama_index.llms.openai import OpenAI    
    # Using OpenAI API for embeddings/llms
    os.environ["OPENAI_API_KEY"] = "sk-None-mslviIwx9iAqddBJqvLbT3BlbkFJYjb3C6AIu1bTt1GmJpvp"   
    llm_model = OpenAI(model=model_name, temperature=0.8, max_tokens=2048)

    return llm_model
