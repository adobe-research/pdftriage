"""
Set up GPT-4 evaluation.

G-Eval code is here:
https://github.com/nlpyang/geval

Outputs of evaluation:
- was an answer provided
- is the extracted source helpful for answering the question
- was the answer correct to the document
"""

import openai
import backoff
from functions import fetch_all, ask_question, ask_question_truncation, ask_question_retrieval_pages, ask_question_retrieval_chunks

def load_prompt():
    pass


@backoff.on_exception(backoff.expo,
                      (openai.error.APIError,
                       openai.error.Timeout,
                       openai.error.APIConnectionError,
                       openai.error.RateLimitError,
                       openai.error.ServiceUnavailableError))

def evaluate(
        context: str,
        question: str,
) -> list[str]:
    
    _response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo-16k",
        messages=[
                    { "role": "system", "content": context},
                    { "role": "user", "content": question},
                 ],
        temperature=2,
        max_tokens=5,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0,
        stop=None,
        n=20,
    )

    all_responses = [
        _response['choices'][i]['message']['content'] 
        for i in range(len(_response['choices']))
    ]

    return all_responses

################################################

import jsonlines
import ast
import json

saved_responses = []
count = 0
 
with jsonlines.open('data/question_filtered.jsonl', 'r') as reader:
    for line in reader:

        if count < 3:
            count += 1
        
            current_dict = line
            
            pdf_url_parsed = line['pdf_url'].split("/")
            extract_path = ("data/valid_json/" + pdf_url_parsed[-1]).replace(".pdf", ".json")
            tree_pdf_path = ("data/valid_metadata/" + pdf_url_parsed[-1]).replace(".pdf", "-metadata.json")

            try:

                responses = ask_question(current_dict['text'], extract_path, tree_pdf_path)
                truncation_responses = ask_question_truncation(current_dict['text'], extract_path, tree_pdf_path)
                retrieval_pages_responses = ask_question_retrieval_pages(current_dict['text'], extract_path, tree_pdf_path)
                retrieval_chunks_responses = ask_question_retrieval_chunks(current_dict['text'], extract_path, tree_pdf_path)

                print("PDF Path")
                print(extract_path)
                print("Question")
                print(current_dict['text'])
                print("GPTriage Responses")
                print(responses)
                print("Truncation Responses")
                print(truncation_responses)
                print("Retrieval Pages Responses")
                print(retrieval_pages_responses)
                print("Retrieval Chunks Responses")
                print(retrieval_chunks_responses)
                print("------------------------------------------")

                saved_responses.append([extract_path, current_dict['text'], responses, truncation_responses, 
                                        retrieval_pages_responses, retrieval_chunks_responses])

            except Exception as e:
                print("Error with following path: " + str(extract_path))
                print("------------------------------------------")

##################################################

import pandas as pd
df = pd.DataFrame(saved_responses, columns=['PDF_Path', 'Question', 'GPT_Triage_Responses', 'Truncation_Responses',
                                            'Retrieval_by_Pages_Responses', 'Retrieval_by_Chunks_Responses'])
df.to_csv('data/saved_responses_for_validation.csv', index=False)
        