import pandas as pd
import json

if __name__ == '__main__':
	df = pd.read_csv("data/processed/docinstruct_tasks_unfiltered.csv")

	for row in df.itertuples():
		print(json.dumps({
			'html': f'<p><b>{row[5]}</b></p><iframe src="{row[4]}" style="width: 100%; height: 400px"></iframe><br /><p>{row[6]}</p>',
			'text': row[6],
			'category': row[5],
			'pdf_url': row[4],
			'annotator': row[2],
			'id': row[0]
		}))
