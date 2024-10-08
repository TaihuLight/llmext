# Prequisites:
# pip install llama-index
# pip install llama-index-core
# pip install llama-index-embeddings-huggingface
# pip install llama-index-postprocessor-flag-embedding-reranker
# pip install git+https://github.com/FlagOpen/FlagEmbedding.git
# git clone --filter=blob:none --quiet https://github.com/FlagOpen/FlagEmbedding.git
# cd FlagEmbedding
# pip install .
# pip install llama-parse llama_index.llms.openai_like llama_index.llms.huggingface llama_index.llms.dashscope


# llama-parse is async-first, running the async code in a notebook requires the use of nest_asyncio
import nest_asyncio, os, subprocess
# shell_command = 'export all_proxy="socks5://127.0.0.1:1080"'
# result_shell = subprocess.run(shell_command, shell=True, capture_output=True, text=True)
# print(result_shell.stdout)

nest_asyncio.apply()
# API access to llama-cloud
os.environ["LLAMA_CLOUD_API_KEY"] = "llx-FTCVt2lKH0tBAHPyj0QjJxPMi42BDvoE3LK3jJP1ii5qsRdr"



from llama_index.core import VectorStoreIndex
from llama_index.core import Settings
from llama_parse import LlamaParse
from copy import deepcopy
from llama_index.core.schema import TextNode
from llama_index.core.node_parser import MarkdownElementNodeParser 
from llama_index.postprocessor.flag_embedding_reranker import FlagEmbeddingReranker
import warnings
from hub_llms import llm_hgface_llamaindex, embed_model, Qwen2

# Disable all warnings
warnings.filterwarnings('ignore') 

# from pydantic import ConfigDict
# model_config = ConfigDict() 
# model_config['protected_namespaces'] = ()

# Using 01.AI API for embeddings/llms
# llm_model = llm_hgface_llamaindex("Qwen/Qwen2-7B-Instruct")
# llm_model = llm_hgface_llamaindex("Qwen/Qwen2.5-7B-Instruct")
llm_model = llm_hgface_llamaindex("meta-llama/Meta-Llama-3-8B-Instruct")
# llm_model = Qwen2()
embed_model = embed_model()

Settings.llm = llm_model
Settings.embed_model = embed_model


def get_page_nodes(docs, separator="\n---\n"):
    """Split each document into page node, by separator."""
    nodes = []
    for doc in docs:
        doc_chunks = doc.text.split(separator)
        for doc_chunk in doc_chunks:
            node = TextNode(
                text=doc_chunk,
                metadata=deepcopy(doc.metadata),
            )
            nodes.append(node)

    return nodes

def get_elements(txtpdf_file, query):
    docs = LlamaParse(result_type="markdown", show_progress=False, do_not_cache=True).load_data(txtpdf_file)
    page_nodes = get_page_nodes(docs)
    node_parser = MarkdownElementNodeParser(llm=llm_model, show_progress=False, num_workers=3)
    nodes = node_parser.get_nodes_from_documents(docs)
    print(len(nodes))
    base_nodes, objects = node_parser.get_nodes_and_objects(nodes)
    print("===content===", objects[0].get_content())
    # dump both indexed tables and page text into the vector index
    recursive_index = VectorStoreIndex(nodes=base_nodes + objects + page_nodes, show_progress=False)
    # print(page_nodes[31].get_content())

    reranker = FlagEmbeddingReranker(
        top_n=5,
        model="BAAI/bge-reranker-large",
    )

    recursive_query_engine = recursive_index.as_query_engine(
        similarity_top_k=5, node_postprocessors=[reranker], verbose=True
    )    

    # query = "Purchases of marketable securities in 2020"
    # response_2 = recursive_query_engine.query(query)
    # print("\n***********New LlamaParse+ Recursive Retriever Query Engine***********")
    # print(response_2)

    # query = "give me the deferred state income tax in 2019-2021 (include +/-)"
    # response_2 = recursive_query_engine.query(query)
    # print("\n***********New LlamaParse+ Recursive Retriever Query Engine***********")
    # print(response_2)
    # print(response_2.source_nodes[0].get_content())

    # query = "current state taxes per year in 2019-2021 (include +/-)"
    # response_2 = recursive_query_engine.query(query)
    # print("\n***********New LlamaParse+ Recursive Retriever Query Engine***********")
    # print(response_2)

    return recursive_query_engine.query(query)



# https://blog.csdn.net/wangyaninglm/article/details/141072088
def getRemovedMD(query_prompt):
    from llama_index.core import VectorStoreIndex, SimpleDirectoryReader

    #从指定目录读取所有文档，并加载数据到内存中
    documents = SimpleDirectoryReader("./data").load_data()
    #创建一个VectorStoreIndex，并使用之前加载的文档来构建索引。
    # 此索引将文档转换为向量，并存储这些向量以便于快速检索。
    index = VectorStoreIndex.from_documents(documents)
    # 创建一个查询引擎，这个引擎可以接收查询并返回相关文档的响应。
    query_engine = index.as_query_engine()
    response = query_engine.query(query_prompt)

    print(response)




if __name__ == '__main__':
    query = "Extract the name of the electrolyte synthesised in Example 1 and its proportaion (do not change numerical precision) of elements may be shown in a Table (include +/-). The electrolyte is represented by a dictionary whose keys are the elements present in the electrolyte and the values are their proportions."
    query = "Extract the name of the electrolyte synthesised in the first example (e.g., Example 1) and its proportion (do not change numerical precision) of elements, which may be shown in a Table (include +/-) or in context. The electrolyte is represented by a dictionary whose keys are the elements present in the electrolyte and the values are their proportions."
    query = """Extract the name of the electrolyte synthesised in the first example (e.g., Example 1) and its ratios (proportions) of elements (e.g., Li, S, P, Br, I) which must include the ratios (proportions) of explicit and implicit elements and they may be shown in a Table or in context.The extracted ratios (proportions) for a electrolyte is represented in a dictionary whose keys are the elements present in the electrolyte and the values are their proportions."""
    # query = "Extract the name of the electrolyte synthesised in Example 1 and its proportion (do not change numerical precision) of elements, which may be shown in a Table (include +/-) or in context. The electrolyte is represented by a dictionary whose keys are the elements present in the electrolyte and the values are their proportions."
    # query = "Extract the name of the electrolyte synthesised in Example 1 and proportions of its explicit and implicit elements. The proportions must include implicit elements and cannot change their numerical precision. The electrolyte is represented with a dictionary whose keys are the elements present in the electrolyte and the values are their proportions."

    # txtpdf_file = "./apple_2021_10k.pdf"
    # txtpdf_file = "./US20180069262A.txt"   # {'Li': 5.40, 'P': 1.00,'S': 4.45, 'Cl': 1.70, 'X': 0.95}
    # response = get_elements(txtpdf_file, query)    
    # txtpdf_file = "./US11258057.txt"     # {'Li': 6, 'P': 1, 'S': 5, 'Cl': 1}
    # response2 = get_elements(txtpdf_file, query)
    # txtpdf_file = "./US11705576.txt"  # {"Li": 1.375, "S": 1.500,"P": 0.375, "Br": 0.150,"I": 0.100}
    # response3 = get_elements(txtpdf_file, query)

    # print("\n***********New LlamaParse + Recursive Retriever Query Engine***********")
    # print(response, "\n===================\n")
    # print(response2, "\n===================\n")
    # print(response3)


    query_extract = "Extract the subwords (phrases) from the above text and count the number of extracted subwords using the rule: replace prepositions (to, for, from, on, in, inside, etc.), verb words, demonstrative pronouns (they, it, one, him, her, itself, our, other, etc.), conjunctions (and, or) and words that express quantity (a, one, two, etc.) with the commas (,)."
    query_extract = "Extract subwords (or phrases) from the above text and count their number using the following steps: (1) Identify and Replace Words: Replace prepositions, verbs, adverbs, pronouns, adpositions, conjunctions, and words expressing quantity with commas. (2) Extract Subwords: Split the modified text by commas and directly output these extracted words in order they appear in the original text. Then, count the resulting phrases."
    
    txtpdf_file = "./US20180069262A.txt"  
    # getRemovedMD(query_extract)
    