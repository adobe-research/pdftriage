import spacy
import json

from pathlib import Path


nlp = spacy.load("quality_model/model-last")

if __name__ == '__main__':
	input_path = Path("questions.jsonl")
	

	with input_path.open() as fp:
		for line in fp:
			data = json.loads(line)
			output = nlp(data['text'])
			cat = max(output.cats.items(), key=lambda x: x[1])
			data['question_quality'] = cat[0]
			del data['html']
			if cat[0] == 'GOOD':
				print(json.dumps(data))
