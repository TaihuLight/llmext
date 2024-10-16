
"""
Universal Part-of-Speech Tagset, https://www.nltk.org/book/ch05.html

ADJ	adjective	new, good, high, special, big, local
ADP	adposition	on, of, at, with, by, into, under
ADV	adverb	really, already, still, early, now
CONJ	conjunction	and, or, but, if, while, although
DET	determiner, article	the, a, some, most, every, no, which
NOUN	noun	year, home, costs, time, Africa
NUM	numeral	twenty-four, fourth, 1991, 14:24
PRT	particle	at, on, out, over per, that, up, with
PRON	pronoun	he, their, her, its, my, I, us
VERB	verb	is, say, told, given, playing, would
.	punctuation marks	. , ; !
X	other	ersatz, esprit, dunno, gr8, univeristy

SHOW DATABASE YIELD name, store   # Information about the storage engine and the store format.
The value is a string formatted as: {storage engine}-{store format}-{major version}.{minor version}

How can I change the store format of my database?
CREATE DATABASE neo4j2 OPTIONS "{"storeFormat: aligned"}"
"""

import nltk, json, csv
import re
from absl import flags
from itertools import groupby
from files_op import read_files

try:
  # Check if NLTK resources are available
  nltk.data.find('tokenizers/punkt')
  nltk.data.find('tokenizers/punkt_tab')
  nltk.data.find('taggers/averaged_perceptron_tagger')
  nltk.data.find('taggers/averaged_perceptron_tagger_eng')
except LookupError:
  nltk.download('punkt')
  nltk.download('punkt_tab')
  nltk.download('averaged_perceptron_tagger')
  nltk.download('averaged_perceptron_tagger_eng')


# Save a 1-D list as a csv file
def save_csv_file(data_list= ['Alice', 'Bob'], csv_file= 'output.csv'):  
  # Writing to the CSV file
  with open(csv_file, mode='w', newline='', encoding='utf-8') as csvfile:
      csv_writer = csv.writer(csvfile)
      for item in data_list:
          csv_writer.writerow([item])  # Write each item as a new row

  print(f"Data saved to {csv_file}")




def getRemovedMDwithnknlp(md_path, rm_duplicates = True):
    with open(md_path, 'r', encoding='utf-8') as f:
        md_doc = f.read()
   
    # Find all matches, 
    # pattern = r'(?:“([^“]*)”|(\S+))'
    # pattern = r'(?:“([^“]*)”|(\S+)|"([^"]+)"|(\S+)|\'([^\']+)\'|(\S+))'
    # matches = re.findall(pattern, md_doc) 
    # list_words = [match[0] if match[0] else match[1] for match in matches]

    list_words = md_doc.split()  
    #  print(list_words)

    for element_id, word in enumerate(list_words):
      list_words[element_id] = list_words[element_id].rstrip('[.,!?;:]')
      if word == 'etc.,' or word == 'etc.' or word == 'such' or word == 'such as' or word == 'e.g.,' or word == 'e.g.':
        list_words[element_id] = ','
        continue
      
      words = nltk.word_tokenize(word)
      pos_tags = nltk.pos_tag(words)

      for _, pos in pos_tags:
          # print(pos_tags)            
          if pos.startswith('DT') or pos.startswith('TO') or pos.startswith('CC') or pos.startswith('RB') or pos.startswith('IN') or pos.startswith('VB') or pos.startswith('WDT'):
              #  print(f"{word} should be remove, then replaced with a comma.")
            list_words[element_id] = ','

    list_words = [key for key, _ in groupby(list_words)]    
    # print(list_words)
    # Construct a string by joining all elements of the list
    result_string = ' '.join(list_words)     
    # markdown_content = re.sub(r'\n\s*\n', '\n\n', str(markdown_content))  
    result_string = re.sub(r' ,', ',', result_string)   # Merge consecutive commas into a single comma
    # print(list_subwords)
    # Split the string and remove spaces from each item
    list_subwords = [item.strip() for item in result_string.split(',')]

    # Remove duplicates except comma
    if rm_duplicates:      
      unique_list = []
      for item in list_subwords:
          item = item.strip()
          # Check if item is not equal to any existing element in unique_list (except for ',')
          if all(item != unique_item for unique_item in unique_list) or item == ',':        
              unique_list.append(item)
      list_subwords = unique_list

    print("Total number of extraced subwords:", len(list_subwords))
    return list_subwords
    

FLAGS = flags.FLAGS


def add_options():
  flags.DEFINE_string('db', default = 'vectordb', help = 'path to vectordb')
  flags.DEFINE_float('threshold', default = 0.5, help = 'threshold')
  flags.DEFINE_integer('max_words_per_entity', default = 3, help = 'maximum words for an entity')
  flags.DEFINE_string('input', default = None, help = 'path to input text')
  flags.DEFINE_string('output', default = 'output.json', help = 'path to output json')


def test_embeddings():
  from langchain_huggingface import HuggingFaceEmbeddings
  # Initialize HuggingFaceEmbeddings
  embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")

  # Example text to generate embeddings for
  texts = [
      "Lithium Lanthanum Zirconate is a promising material.",
      "This is another example sentence for embedding."
  ]

  # Generate embeddings
  embeddings = embedding_model.embed_documents(texts)

  # Output the embeddings
  for text, embedding in zip(texts, embeddings):
      print(f"Text: {text}")
      print(f"Embedding: {embedding}\n")


def search_entities(words):
  # from langchain.embeddings.huggingface import HuggingFaceEmbeddings
  from langchain_huggingface import HuggingFaceEmbeddings
  from langchain_community.vectorstores import Neo4jVector

  embeddings = HuggingFaceEmbeddings(model_name = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2") 
  embedding_model = HuggingFaceEmbeddings(model_name="distilbert-base-nli-mean-tokens")  

  paper_graph = Neo4jVector.from_existing_graph(
    embedding=embedding_model,
    url="bolt://103.6.49.76:7687",
    username="neo4j",
    password="19841124",
    index_name="paper_index",
    database="neo4j",
    node_label="Paper",
    text_node_properties=["abstract", "title"],
    embedding_node_property="paper_embedding3",
  )

  paper_graph = Neo4jVector.from_existing_graph(
    embedding=embedding_model,
    url="bolt://103.6.49.76:7687",
    username="neo4j",
    password="19841124",
    index_name="bbc_index",
    database="mner",
    node_label="Paper",
    text_node_properties=["formula", "name"],
    embedding_node_property="bbc_embedding",
  )

  # Creating Embeddings from existing graph, https://medium.com/thedeephub/building-a-graph-database-with-vector-embeddings-a-python-tutorial-with-neo4j-and-embeddings-277ce608634d
  existing_graph = Neo4jVector.from_existing_graph(embedding=embeddings, username="neo4j", password="19841124", database="mner", url="bolt://103.6.49.76:7687",
      index_name="embedding_index", node_label="BromideBasedCeramics", text_node_properties=["name", "formula"], embedding_node_property="embedding",)  
  rst = existing_graph.similarity_search("Lithium Lanthanum Zirconate", k=5)

  neo4j_store = Neo4jVector(username="neo4j", password="19841124", database="mner", url="bolt://103.6.49.76:7687", embedding=embeddings)
  rst = neo4j_store.create_new_keyword_index(["name", "formula", "id"])

  print(rst)

  retriever = existing_graph.as_retriever(search_type = "similarity_score_threshold", search_kwargs = {"score_threshold": 0.6})
  tokens = list()

  # words = sentence.split(' ')
  # for n_words in range(1, FLAGS.max_words_per_entity + 1):
  #   for offset in range(n_words):
  #     for i in range(offset, len(words), n_words):
  #       substring = ' '.join(words[i:i + n_words])
  #       matches = retriever.invoke(substring)
  #       if len(matches):
  #         token_start_pos = sentence.find(substring)
  #         tokens.append((substring, sentence_start_pos + token_start_pos))
  # results = [(token[0],token[1],token[1] + len(token[0])) for token in tokens]
  # with open(FLAGS.output, 'w') as f:
  #   f.write(json.dumps(list(set(results))))



def retrieve_entities(words):
  from llama_index.graph_stores.neo4j import Neo4jPGStore
  from llama_index.graph_stores.neo4j import Neo4jPropertyGraphStore
  from llama_index.core.retrievers import  CustomPGRetriever, VectorContextRetriever, TextToCypherRetriever 
  from llama_index.vector_stores.neo4jvector import Neo4jVectorStore
  from llama_index.core import VectorStoreIndex
  from llama_index.embeddings.huggingface import HuggingFaceEmbedding
  from hub_llms import embed_model

# URL web server: http://103.6.49.76:7474/browser/
  graph_store = Neo4jPropertyGraphStore(username="neo4j", password="19841124", database="neo4j", url="bolt://103.6.49.76:7687", )
  graph_store = Neo4jPGStore(username="neo4j", password="19841124", database="mner2", url="bolt://103.6.49.76:7687", )
  
  max_words_per_entity = 3
  neo4j_vector_store = Neo4jVectorStore(username="neo4j", password="19841124", database="neo4j", url="bolt://103.6.49.76:7687", 
                                        node_label ="Paper", embedding_dimension = 1536, index_name="embedding_index", text_node_property="name",)
  x = neo4j_vector_store.retrieve_existing_index()
  print("====", x)

  loaded_index = VectorStoreIndex.from_vector_store(vector_store=neo4j_vector_store, embed_model=HuggingFaceEmbedding(model_name="BAAI/bge-small-en-v1.5"))

  vector_retriever = VectorContextRetriever(
              graph_store = graph_store,
              include_text = True,
              embed_model = embed_model,
              vector_store = neo4j_vector_store,
              similarity_top_k = 6,
              path_depth = 1,
          )

  for n_words in range(1, max_words_per_entity + 1):
    for offset in range(n_words):
      for i in range(offset, len(words), n_words):
        substring = ' '.join(words[i:i + n_words])
        nodes_matched = vector_retriever.retrieve(substring)
        print(nodes_matched)


if __name__ == '__main__':
    str1 = "The invention relates to a sulfide solid electrolyte, an electrode mix and a lithium ion battery. "
    str2 = "In recent years, with rapid spread of information-related equipment or communication equipment such as PCs, video cameras, mobile phones, etc., development of a battery."
        
    txtpdf_file = "./data/US20180069262A.txt" 

    paper_mdifles = read_files("./archive", ".md")
    for paper_md in paper_mdifles:
        list_subwords = getRemovedMDwithnknlp(paper_md, False)
        save_csv_file(list_subwords, paper_md[:-3]+'.csv')
        
        list_subwords = getRemovedMDwithnknlp(paper_md, True)
        save_csv_file(list_subwords, paper_md[:-3]+'_rmd.csv')


    # retrieve_entities("electrolyte")
    # test_embeddings()