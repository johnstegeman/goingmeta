import os
from neo4jconnector import Neo4jConnection
from utils import getNLOntology
from openai import OpenAI
from rdflib import Graph

####### STEP1: GET THE UNSTRUCTURED CONTENT #########################

# for each of the files in the 'content' directory
with open('content/hockney-mr-and-mrs-clark-and-percy.txt', 'r') as file:
   content = file.read().replace('\n', '')


####### STEP2: GET THE ONTOLOGY #####################################
g = Graph()
g.parse("ontologies/art.ttl")

# OPTION 1 : Ontology in standard serialisation
ontology = g.serialize(format="ttl")

# OPTION 2 : Natural language description of the ontology
ontology = getNLOntology(g)


####### STEP3: PROMPT THE LLM ####################################### 

client = OpenAI(
    # This is the default and can be omitted
    api_key=os.environ.get("OPENAI_API_KEY"),
)

system = (
    "You are an expert in extracting structured information out of natural language text. "
    "You extract entities with their attributes and relationships between entities. "
    "You can produce the output as RDF triples or as Cypher write statements on request. "      
)

prompt = '''Given the ontology below run your best entity extraction over the content.
 The extracted entities and relationships must be described using exclusively the terms in the ontology 
 and in the way they are defined. This means that for attributes and relationships you will respect the domain and range constraints.
 You will never use terms not defined in the ontology. 
Return the output as Cypher using merge to allow for linkage of nodes from multiple passes. 
Absolutely no comments on the output. Just the structured output. ''' + '\n\nONTOLOGY: \n ' + ontology + '\n\nCONTENT: \n ' + content 

# if you want to inspect...
#print(prompt)

chat_completion = client.chat.completions.create(
    messages=[
        {
          'role': 'system',
          'content': system,
        },
        {
          'role': 'user',
          'content': prompt ,
        }
          ],
    model="gpt-4o",
)

cypher_script = chat_completion.choices[0].message.content[3:-3]
# The Cypher generated by the LLM 
print(cypher_script)


####### STEP4: WRITE CONTENT TO THE DB ##############################

uri = "bolt://localhost:7687"
user = "neo4j"  # Change if you've modified the default username
password = "neoneoneo"  # Change to your actual password
conn = Neo4jConnection(uri, user, password)

# Run the Cypher script and get the results
result = conn.run_cypher(cypher_script)

# Close the connection
conn.close()

