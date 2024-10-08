#
import json
from neomodel import (StructuredNode, StringProperty, RelationshipTo, config)

data = []

with open("archive/sample_2.json") as user_file:
    for line in user_file:
        data.append(json.loads(line))

config.DATABASE_URL = 'bolt://neo4j:19841124@103.6.49.76:7687'
config.DATABASE_NAME = 'neo4j'
config.FORCE_TIMEZONE = True


class Paper(StructuredNode):
    uid = StringProperty(unique_index=True)
    submitter = StringProperty()
    title = StringProperty()
    comments = StringProperty()
    journal_ref = StringProperty()
    doi = StringProperty()
    report_no = StringProperty()
    categories = StringProperty()
    abstract = StringProperty()
    update_date = StringProperty()
    
    authors = RelationshipTo("Author", 'AUTHORED_BY')
    versions = RelationshipTo("Version", "HAS_VERSION")


class Author(StructuredNode):
    name = StringProperty(unique_index=True)


class Version(StructuredNode):
    version = StringProperty()
    created = StringProperty()


def clear_nodes():
    nodes = Paper.nodes.all()  # Replace Person with your model class if needed
    print("----", len(nodes))
    # Delete each node
    for node in nodes:
        node.authors.disconnect_all()
        node.versions.disconnect_all()
        node.save()  # Save changes to the database
        node.delete()
        

    nodes = Author.nodes.all()  # Replace Person with your model class if needed
    # Delete each node
    for node in nodes:
        node.delete()
    
    nodes = Version.nodes.all()  # Replace Person with your model class if needed
    # Delete each node
    for node in nodes:
        node.delete()



def create_nodes_and_relationships(data):
    paper = Paper(uid=data['id'], submitter=data['submitter'], 
                title=data['title'], comments=data['comments'],
                journal_ref=data['journal-ref'], doi=data['doi'],
                report_no=data['report-no'],categories=data['categories'],
                abstract=data['abstract'], update_data=data['update_date']).save()

    for author in data['authors_parsed']:
        author_node = Author(name=" ".join(author)).save()
        paper.authors.connect(author_node)
    
    for version in data['versions']:
        version_node = Version(version=version['version'],
                                created=version['created']).save()
        paper.versions.connect(version_node)

# clear_nodes()

create_nodes_and_relationships(data[0]) 
with open("archive/sample_2.json") as user_file:
# with open("archive/arxiv-metadata-oai-snapshot.json") as user_file:
    for line in user_file:
        try:
            create_nodes_and_relationships(json.loads(line))
        except Exception as e:
            print(e)


from langchain_community.vectorstores import Neo4jVector
from langchain_huggingface import HuggingFaceEmbeddings
embedding_model = HuggingFaceEmbeddings(model_name="distilbert-base-nli-mean-tokens")
from dotenv import load_dotenv

load_dotenv()

# Create embeddings for the paper nodes
# paper_graph = Neo4jVector.from_existing_graph(
#     embedding=embedding_model,
#     url="bolt://localhost:7687",
#     username="neo4j",
#     password="19841124",
#     index_name="paper_index",
#     database="neo4j",
#     node_label="Paper",
#     text_node_properties=["abstract", "title"],
#     embedding_node_property="paper_embedding",
# )

from pprint import pprint

# result = paper_graph.similarity_search("dark matter field fluid model")
# pprint(result[0].page_content)


