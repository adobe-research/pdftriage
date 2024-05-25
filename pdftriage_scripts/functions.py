from __future__ import annotations
from pathlib import Path
from extract_metadata import extract_to_tree, Node

import numpy
import openai
import json


#############################

functions = [
    {
        "name": "fetch_pages",
        "description": "Fetch the content of specified pages from the document.",
        "parameters": {
            "type": "object",
            "properties": {
                "pages": {
                    "type": "array",
                    "items": {
                        "type": "number"
                    },
                    "description": "The list of pages to fetch."
                }
            },
            "required": ["pages"]
        }
    },
    {
        "name": "fetch_section",
        "description": "Fetch the content of a specified section.",
        "parameters": {
            "type": "object",
            "properties": {
                "section_title": {
                    "type": "string",
                    "description": "The title of the section to fetch."
                }
            },
            "required": ["section_title"]
        }
    },
    {
        "name": "search",
        "description": "Search the document for a string query.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search term."
                }
            },
            "required": ["query"]
        }
    }
]


def fetch_pages(
        tree: dict,
        pages: list[int],
) -> str:
    
    content = ""
    for key in tree['pages'].keys():
        if key in pages:
            content += tree['pages'][key] + "\n"
    
    #content = (" ").join(content.strip().split(" ")[:1])
    content = content.strip()
    return content


def fetch_section(
        tree: dict,
        extract: dict,
        section: str,
) -> str:

    content = ""
    for section in tree['sections']:
        if section == section['title']:
            content = content + " " + section['text']
    
    #content = (" ").join(content.strip().split(" ")[:1])
    content = content.strip()
    return content

def fetch_all(
        json_uploaded: dict
) -> str:

    content = ""
    for section in json_uploaded['sections']:
        content = content + " " + section['text']
    return content.strip()

class VectorStore:
    
    def __init__(
            self,
            vectors: list[list[float]] | list[numpy.array]
    ) -> None:
        self.vectors = numpy.array(vectors)
    
    
    def neighbors(
            self,
            query: list[float] | numpy.array,
            k: int
    ) -> list[int]:
        query = numpy.array(query)
        similarities = numpy.dot(self.vectors, query.T)
        document_similarities = sorted([
            (similarity, ix) for ix, similarity in enumerate(similarities)
        ], reverse=True, key=lambda t: t[0])

        return document_similarities[:k]


def embed(
        text: list[str],
        model: str = "text-embedding-ada-002"
) -> numpy.ndarray:
    """
    We're going to use the OpenAI API to embed the texts for retrieval.
    """
    embedding = openai.Embedding.create(
        input=text,
        model=model
    )

    return [numpy.array(data['embedding']) for data in embedding['data']]


def search(
        tree: Node,
        extract: list[dict],
        query: str,
) -> str:
    long_document = []
    page_ids = []

    for page in tree['pages']:
        page_content = fetch_pages(tree, [page])
        if not page_content.strip(): continue
        page_ids.append(page)
        long_document.append(page_content)

    doc_embeddings = embed(long_document)

    query_embedding = embed([query])[0]

    v = VectorStore(doc_embeddings)

    neighbors = v.neighbors(query_embedding, k=4)
    neighbors = sorted([page_ids[n] for _, n in neighbors])

    return fetch_pages(tree, neighbors)


def execute_function_call(
        message: dict,
        extract,
        tree,
) -> tuple[str, dict[str, str]]:
    arguments = json.loads(message["function_call"]["arguments"])
    action = {}

    if message["function_call"]["name"] == "fetch_pages":
        pages = arguments["pages"]
        content = fetch_pages(tree, pages)
        if len(pages) == 1:
            noun = f"page {pages[0]}"
        else:
            noun = "pages " + " ".join(str(p) for p in pages)

        action = { "verb": "fetching", "noun": noun }
    elif message["function_call"]["name"] == "fetch_section":
        action = { "verb": "fetching", "noun": arguments["section_title"] }
        content = fetch_section(tree, extract, arguments["section_title"])
    elif message["function_call"]["name"] == "search":
        action = { "verb": "searching", "noun": arguments["query"] }
        content = search(tree, extract, arguments["query"])
    else:
        content = f"Error: function {message['function_call']['name']} does not exist"
    return content, action


def load_extract(
        document: str
) -> list[dict]:
    extract_path = Path(document)

    with extract_path.open() as f_extract:
        extract = json.load(f_extract)

    return extract['elements']

def load_tree(
        document: str
) -> list[dict]:
    tree_path = Path(document)

    with tree_path.open() as f_tree:
        tree = json.load(f_tree)

    return tree

def ask_question(
        question: str,
        extract_path: str,
        tree_path: str
) -> tuple[str, list[dict]]:
   
    extract = load_extract(extract_path)
    tree = load_tree(tree_path)
    actions = []

    metadata = {
        'pages': tree['pages'],
        'sections': tree['sections']
    }

    messages = [
        {
            'role': 'system',
            'content': f"""
You are an expert document question answering system. You answer questions by finding relevant content in the document and answering questions based on that content. You can summarize the document by fetching the first several pages. Document metadata: {json.dumps(metadata)}
""".strip()
        },
        {
            'role': 'user',
            'content': question
        }
    ]

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo-16k", #"gpt-3.5-turbo-0613",
            messages=messages,
            functions=functions,
            function_call="auto",
        )
    except:
        
        for key in tree['pages']:
            tree['pages'][key] = (" ").join(tree['pages'][key].split(" ")[:256])
        for i in range(0, len(tree['sections'])):
            tree['sections'][i]["text"] = (" ").join(tree['sections'][i]["text"].split(" ")[:256])
        
        messages = [
            {
                'role': 'system',
                'content': f"""
    You are an expert document question answering system. You answer questions by finding relevant content in the document and answering questions based on that content. You can summarize the document by fetching the first several pages. Document metadata: {json.dumps(metadata)}
    """.strip()
            },
            {
                'role': 'user',
                'content': question
            }
        ]

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo-16k", #"gpt-3.5-turbo-0613",
            messages=messages,
            functions=functions,
            function_call="auto",
        )

    ######################################################################################################

    assistant_message = response["choices"][0]["message"]
    messages.append(assistant_message)

    if assistant_message.get("function_call"):
        results, action = execute_function_call(assistant_message, extract, tree)
        actions.append(action)
        messages.append({"role": "function", "name": assistant_message["function_call"]["name"], "content": results})

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo-16k", #"gpt-3.5-turbo-16k",
        messages=messages,
    )

    return response["choices"][0]["message"]["content"], actions







##################################################

import tiktoken

def truncate(input_text, max_token_limit, model_name="gpt-3.5-turbo"):

    
    encoder = tiktoken.encoding_for_model(model_name)
    encoded_text = encoder.encode(input_text)[:max_token_limit]
    decoded_text = encoder.decode(encoded_text)
    return decoded_text

def ask_question_truncation(
        question: str,
        extract_path: str,
        tree_path: str
) -> tuple[str, list[dict]]:
   
    extract = load_extract(extract_path)
    tree = load_tree(tree_path)
    actions = []

    context = ""
    for section in tree['sections']:
        context += section['text'] + " "

    context = truncate(context, 3000, "gpt-3.5-turbo")

    messages = [
        {
            'role': 'system',
            'content': f"""
You are an expert document question answering system. You answer questions by finding relevant content in the document and answering questions based on that content. Document: {context}
""".strip()
        },
        {
            'role': 'user',
            'content': question
        }
    ]

    response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo", #"gpt-3.5-turbo-0613",
            messages=messages,
            #functions=functions,
            #function_call="auto"
        )

    return response["choices"][0]["message"]["content"]

######################################################################################################

def perform_retrieval(question: str, documents: list[str]):
    
    page_ids = []
    long_documents = []

    for i, document in zip(range(len(documents)), documents):
        page_ids.append(i)
        long_documents.append(document)

    doc_embeddings = embed(long_documents)

    query_embedding = embed([question])[0]

    v = VectorStore(doc_embeddings)

    neighbors = v.neighbors(query_embedding, k=4)
    neighbors = sorted([page_ids[n] for _, n in neighbors])
    
    #print("neighbors")
    #print(len(documents))
    #print(neighbors)

    #print("Returned document")
    #print(len(documents))
    #print(documents[neighbors[0]])
    
    return documents[neighbors[0]]

def ask_question_retrieval_pages(
        question: str,
        extract_path: str,
        tree_path: str
) -> tuple[str, list[dict]]:
   
    extract = load_extract(extract_path)
    tree = load_tree(tree_path)
    actions = []

    pages = []
    for key in tree['pages'].keys():
        pages.append(tree['pages'][key])

    context = perform_retrieval(question, pages)

    messages = [
        {
            'role': 'system',
            'content': f"""
You are an expert document question answering system. You answer questions by finding relevant content in the document and answering questions based on that content. Document: {context}
""".strip()
        },
        {
            'role': 'user',
            'content': question
        }
    ]

    response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo", #"gpt-3.5-turbo-0613",
            messages=messages,
            #functions=functions,
            #function_call="auto"
        )

    return response["choices"][0]["message"]["content"]

######################################################################################################

import re

def divide_into_chunks(text, chunk_size=100):
    words = re.findall(r'\b\w+\b', text)
    chunks = [words[i:i + chunk_size] for i in range(0, len(words), chunk_size)]
    chunked_texts = [' '.join(chunk) for chunk in chunks]
    return chunked_texts

def ask_question_retrieval_chunks(
        question: str,
        extract_path: str,
        tree_path: str
) -> tuple[str, list[dict]]:
   
    extract = load_extract(extract_path)
    tree = load_tree(tree_path)
    actions = []

    total_context = ""
    for key in tree['pages'].keys():
        total_context += tree['pages'][key] + " "
    
    chunks = divide_into_chunks(total_context, 100)
    context = perform_retrieval(question, chunks)

    messages = [
        {
            'role': 'system',
            'content': f"""
You are an expert document question answering system. You answer questions by finding relevant content in the document and answering questions based on that content. Document: {context}
""".strip()
        },
        {
            'role': 'user',
            'content': question
        }
    ]

    response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo", #"gpt-3.5-turbo-0613",
            messages=messages,
            #functions=functions,
            #function_call="auto"
        )

    return response["choices"][0]["message"]["content"]