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

from hub_llms import llm_hgface_llamaindex, embed_model, Qwen2

# Using 01.AI API for embeddings/llms
llm_model = llm_hgface_llamaindex("Qwen/Qwen2-7B-Instruct")
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
    docs = LlamaParse(result_type="markdown").load_data(txtpdf_file)
    page_nodes = get_page_nodes(docs)
    node_parser = MarkdownElementNodeParser(llm=llm_model, num_workers=3)
    nodes = node_parser.get_nodes_from_documents(docs)
    base_nodes, objects = node_parser.get_nodes_and_objects(nodes)
    print(objects[0].get_content())
    # Dump both indexed tables and page text into the vector index
    recursive_index = VectorStoreIndex(nodes=base_nodes + objects + page_nodes, show_progress=False)
    # print(page_nodes[31].get_content())

    reranker = FlagEmbeddingReranker(
        top_n=5,
        model="BAAI/bge-reranker-large",
    )

    recursive_query_engine = recursive_index.as_query_engine(
        similarity_top_k=5, node_postprocessors=[reranker], verbose=True
    )
    print(len(nodes))

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


if __name__ == '__main__':
    query = "Extract the name of the electrolyte synthesised in Example 1 and its proportaion (do not change numerical precision) of elements may be shown in a Table (include +/-). The electrolyte is represented by a dictionary whose keys are the elements present in the electrolyte and the values are their proportions."
    query = "Extract the name of the electrolyte synthesised in the first example (e.g., Example 1) and its proportion (do not change numerical precision) of elements, which may be shown in a Table (include +/-) or in context. The electrolyte is represented by a dictionary whose keys are the elements present in the electrolyte and the values are their proportions."
    query = """Extract the name of the electrolyte synthesised in the first example (e.g., Example 1) and its proportion of elements which must include the proportion of implicit elements and they may be shown in a Table (include +/-) or in context.The extracted elements and their proportion for a electrolyte is defined in the form of a dictionary whose keys are the elements present in the electrolyte and the values are their proportions."""
    query = "Extract the name of the electrolyte synthesised in Example 1 and its proportion (do not change numerical precision) of elements, which may be shown in a Table (include +/-) or in context. The electrolyte is represented by a dictionary whose keys are the elements present in the electrolyte and the values are their proportions."
    query = "Extract the name of the electrolyte synthesised in Example 1 and proportions of its explicit and implicit elements. The proportions must include implicit elements and cannot change their numerical precision. The electrolyte is represented with a dictionary whose keys are the elements present in the electrolyte and the values are their proportions."

    # txtpdf_file = "./apple_2021_10k.pdf"
    txtpdf_file = "./US20180069262A.txt"   # {'Li': 5.40, 'P': 1.00,'S': 4.45, 'Cl': 1.70, 'X': 0.95}
    response = get_elements(txtpdf_file, query)    
    txtpdf_file = "./US11258057.txt"     # {'Li': 6, 'P': 1, 'S': 5, 'Cl': 1}
    response2 = get_elements(txtpdf_file, query)
    txtpdf_file = "./US11705576.txt"  # {"Li": 1.375, "S": 1.500,"P": 0.375, "Br": 0.150,"I": 0.100}
    response3 = get_elements(txtpdf_file, query)

    print("\n***********New LlamaParse + Recursive Retriever Query Engine***********")
    print(response, "\n===================\n")
    print(response2, "\n===================\n")
    print(response3)