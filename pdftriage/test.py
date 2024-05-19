from pydantic import BaseModel, Field
from typing import Optional, List, Union, Literal
from langchain.chains.openai_functions import create_openai_fn_chain, create_structured_output_chain
from langchain.chat_models import ChatOpenAI, AzureChatOpenAI
from langchain.prompts import ChatPromptTemplate, HumanMessagePromptTemplate
from langchain.schema import HumanMessage, SystemMessage


class FetchPages(BaseModel):
    """Fetch the content of specific pages from the document."""
    name: Literal["fetch_pages"]
    page_numbers: List[int] = Field(..., description="the list of required page numbers")


class FetchSection(BaseModel):
    """Fetch the content of a specific section within the document."""
    name: Literal["fetch_section"]
    section_title: str = Field(..., description="the name of the relevant section")
    section_id: int = Field(..., description="the id of the relevant section")


class FetchAll(BaseModel):
    """Fetch the full contents of the document."""
    name: Literal["fetch_all"]


class SearchDocument(BaseModel):
    """Search the document."""
    name: Literal["search_document"]
    query: str


class Fetch(BaseModel):
    """Fetch the relevant context necessary to answer the question. You can call as many functions as you need, but you should call `SearchDocument` 99% of the time."""
    function: Union[SearchDocument, FetchAll, FetchSection, FetchPages] = Field(..., description="which function to call, with its appropriate arguments.", discriminator="name")


simplified_tree = {
    "pages": [
      1,
      2,
      3,
      4,
      5,
      6,
      7,
      8,
      9,
      10,
      11
    ],
    "sections": [
      {
        "title": "Tree of Thoughts: Deliberate Problem Solving with Large Language Models ",
        "section_id": 0,
        "pages": [
          1
        ]
      },
      {
        "title": "arXiv:2305.10601v1  [cs.CL]  17 May 2023 ",
        "section_id": 1,
        "pages": [
          1
        ]
      },
      {
        "title": "Abstract ",
        "section_id": 2,
        "pages": [
          1
        ]
      },
      {
        "title": "1 Introduction ",
        "section_id": 3,
        "pages": [
          1
        ]
      },
      {
        "title": "2 Background ",
        "section_id": 4,
        "pages": [
          2
        ]
      },
      {
        "title": "3 Tree of Thoughts: Deliberate Problem Solving with LM ",
        "section_id": 5,
        "pages": [
          3
        ]
      },
      {
        "title": "4 Experiments ",
        "section_id": 6,
        "pages": [
          4
        ]
      },
      {
        "title": "5 Related Work ",
        "section_id": 7,
        "pages": [
          8
        ]
      },
      {
        "title": "6 Discussion ",
        "section_id": 8,
        "pages": [
          9
        ]
      },
      {
        "title": "References ",
        "section_id": 9,
        "pages": [
          10
        ]
      }
    ]
  }

triage_llm = ChatOpenAI(model_name="gpt-3.5-turbo-16k-0613",
                        temperature=0.,
                        request_timeout=120)

triage_prompt_messages = [
    SystemMessage(
        content=
        """
You are a helpful AI assistant that finds relevant parts of a document that answer a user's question. You should use SearchDocument 99\% of the time. Do not answer the QUESTION directly and use the TABLE_OF_CONTENTS as a guide.
        """.strip()
    ),
    HumanMessagePromptTemplate.from_template(
"""
TABLE_OF_CONTENTS : {document_metadata},
QUESTION : {question}
""".strip()
    )
]

triage_prompt = ChatPromptTemplate(messages=triage_prompt_messages)

#ToDo : Currenlty fails in openai_functions.py", line 28 when it answers directly
triage_function_chain = create_openai_fn_chain(
    [FetchPages, FetchSection, FetchAll, SearchDocument],
    llm=triage_llm,
    prompt=triage_prompt,
    verbose=True,
)


question = "Can you ELI5 their creative writing task?"
# question = "Can you ELI5 about the game of 24?"
# I get as response : 
# {'name': 'compose', 'arguments': {'list_of_functions_with_arguments': [['fetch_section', {'section': '2 Background'}], ['fetch_section', {'section': '3 Tree of Thoughts: Deliberate Problem Solving with LM'}]]}}
# a search would be so much better than fetch section. Also, section titles do not exactly match (although we can handle it with postprocessing)

# question = "Can you find me information about the game of 24?"
# I get as response : 
# {'name': 'compose', 'arguments': {'list_of_functions_with_arguments': [['search', {'query': 'game of 24'}]]}}

# question = "What is the closest related work to this paper?"
# I get as response
# {'name': 'fetch_section', 'arguments': {'section': '5 Related Work'}}
simplified_tree_str = str(simplified_tree)

triage_function_call_response = triage_function_chain.run(
    {
        "document_metadata": simplified_tree_str,
        "question": question,
    }
)

print(triage_function_call_response)
print(type(triage_function_call_response))

