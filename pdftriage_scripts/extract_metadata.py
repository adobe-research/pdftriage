from __future__ import annotations
from pathlib import Path
from pydantic import BaseModel
from typing import Any

import click
import json
from pathlib import Path


def part_to_tuple(
        part: str
) -> tuple[str, int]:
    if '[' in part:
        type, num = part.split('[')
        return type, int(num[:-1])
    return part, 1

meta_sections = []

class Node(BaseModel):
    page: int | None = None
    type: str
    text: str

    children: dict[str, Node] = {}

    @property
    def pages(self) -> list[str]:
        #return self.page
        if len(self.children) == 0 and self.page: return [self.page]
        #elif len(self.children) == 0 and not self.page: return []

        return sorted(set([p for c in self.children.values() for p in c.pages]))
    
    @property
    def sections(self) -> list[dict[str, Any]]:
        
        if len(self.children) == 0:
            return [[{'pages': self.pages}, {'type': self.type}, 
                     {'title': self.title}, {'text': self.text}]]
        else:
            sections = [{'pages': self.pages}, {'type': self.type}, 
                        {'title': self.title}, {'text': self.text}]
            for _, child in self.children.items():
                sections.extend(child.sections)
            return sections
    
    @property
    def title(self) -> str | None:
        if len(self.children) == 0:
            return None
        
        for _, child in self.children.items():
            if child.type == 'Title':
                return child.text
            elif child.type.startswith('H'):
                return child.text
            else:
                if child.title != None:
                    return child.title
        
        return None


def extract_to_tree(
        extract: list[dict]
) -> Node:
    root = Node(
        type='//',
        text='',
    )

    for element in extract:
        path = Path(element['Path'])

        cur = root
        for part in path.parts[1:-1]:
            part_tup = part_to_tuple(part)

            if part_tup in cur.children:
                cur = cur.children[part_tup]
            else:
                child = Node(type=part_tup[0], text='')
                cur.children[part_tup] = child
                cur = child
        
        type, num = part_to_tuple(path.parts[-1])
        cur.children[(type, num)] = \
            Node(page=element.get('Page', None), type=type, text=element.get('Text', ''))
    
    return root

def extract_to_tree_v2(
        extract: list[dict]
) -> tuple: 

    #print("Extract")
    #print(len(extract))
    #print(extract[0])
    #print("filePaths" in extract[0])
    #print(extract[2])
    #print("filePaths" in extract[2])

    page_to_text = {}
    page_to_figures = {}

    pages = []
    page_to_texts_and_figures = {}

    for box in extract:

        if "Page" in box:

            current_page = box['Page']
            if current_page not in pages:
                pages.append(current_page)

            #print(box.keys())
            #
            # print(box['attributes'].keys())
            #print(box)
            #print("--------------------")

            if "filePaths" in box:
                current_figure = box["filePaths"]
                if current_page in page_to_figures:
                    page_to_figures[current_page].append(current_figure)
                    page_to_texts_and_figures[current_page].append(current_figure)
                else:
                    page_to_figures[current_page] = [current_figure]
                    page_to_texts_and_figures[current_page] = [current_figure]
            else:
                if 'Text' in box:
                    current_text = box['Text']
                    if current_page in page_to_text:
                        page_to_text[current_page].append(current_text)
                        page_to_texts_and_figures[current_page].append(current_text)
                    else:
                        page_to_text[current_page] = [current_text]
                        page_to_texts_and_figures[current_page] = [current_text]
                else:
                    if "Kids" in box:
                        kids = box['Kids']
                        texts = [kid['Text'] for kid in kids if 'Text' in kids]
                        if len(texts) > 0:
                            for current_text in texts:
                                if current_page in page_to_text:
                                    page_to_text[current_page].append(current_text)
                                    page_to_texts_and_figures[current_page].append(current_text)
                                else:
                                    page_to_text[current_page] = [current_text]
                                    page_to_texts_and_figures[current_page] = [current_text]
                    #else:
                        #print("Error for this past box!")

    ####################

    return pages, [page_to_texts_and_figures[page] for page in page_to_texts_and_figures], page_to_text, page_to_figures

########################

def extract_to_tree_v3(
        extract: list[dict]
) -> tuple: 

    #print("Extract")
    #print(len(extract))
    #print(extract[0])
    #print("filePaths" in extract[0])
    #print(extract[1])
    #print("filePaths" in extract[1])
    #print(extract[11])
    #print("filePaths" in extract[2])

    def part_to_tuple_v3(
            part: str
    ) -> tuple[str, int]:
        if '[' in part:
            type, num = part.split('[')
            return type, int(num[:-1])
        return part, 1

    root = Node(
        type='root',
        text='',
    )

    for element in extract:
        #path = Path(element['Path'])

        if "Text" in element and "Page" in element:

            current_section = element['Path'].replace("//Document/","")
            current_section_split = current_section.split("/")

            cur = root
            for section in current_section_split:
                part_tup = part_to_tuple_v3(section)

                if part_tup in cur.children:
                    cur = cur.children[part_tup]
                else:
                    child = Node(type=part_tup[0], text='')
                    cur.children[part_tup] = child
                    cur = child
            
            #type, num = part_to_tuple(path.parts[-1])
            type, num = part_to_tuple(current_section_split[-1])
            cur.children[(type, num)] = Node(page=element['Page'], type=type, text=element['Text'])
    
    return root

########################

def extract_to_tree_v4(
        extract: list[dict]
) -> tuple: 

    #print("Extract")
    #print(len(extract))
    #print(extract)

    section_to_metadata = {}
    page_to_text = {}
    section_to_figures = {}
    section_to_tables = {}

    for element in extract:

        current_path = element['Path'].replace("//Document/","")
        current_path_split = current_path.split("/")
        current_section = current_path_split[0]

        if "Text" in element and "Page" in element:
            
            if current_section not in section_to_metadata:
                section_to_metadata[current_section] = {"title": "", "pages": [], "text": "", "header_type": ""}
                current_metadata = section_to_metadata[current_section]
            else:
                current_metadata = section_to_metadata[current_section]
            
            if "Title" in current_path:
                current_metadata['title'] = element['Text']
                current_metadata['header_type'] = "Title"
            elif "H1" in current_path and (len(current_metadata['title']) == 0 or current_metadata['header_type'] == "H2"):
                current_metadata['title'] = element['Text']
                current_metadata['header_type'] = "H1"
            elif "H2" in current_path and len(current_metadata['title']) == 0:
                current_metadata['title'] = element['Text']
                current_metadata['header_type'] = "H2"
            else:
                current_metadata['text'] = current_metadata['text'] + " " + element['Text']

            if element['Page'] + 1 not in current_metadata['pages']:
                current_metadata['pages'].append(element['Page'] + 1)
            
            section_to_metadata[current_section] = current_metadata

            ####################

            if element['Page'] + 1 in page_to_text:
                page_to_text[element['Page'] + 1] = page_to_text[element['Page'] + 1] + " " + element['Text']
            else:
                page_to_text[element['Page'] + 1] = element['Text']

        # if "Figure" in current_path:
        #     if current_section not in section_to_figures:
        #         if "Text" in element:
        #             caption = element['Text']
        #         else:
        #             caption = ""
        #         section_to_figures[current_section] = [{"page": element['Page'] + 1, "path": current_path, "caption": caption}]
        #     else:
        #         section_to_figures[current_section].append([{"page": element['Page'] + 1, "path": current_path, "caption": caption}])

        # if "Table" in current_path:
        #     if current_section not in section_to_tables:
        #         if "Text" in element:
        #             caption = element['Text']
        #         else:
        #             caption = ""
        #         section_to_tables[current_section] = [{"page": element['Page'] + 1, "path": current_path, "caption": caption}]
        #     else:
        #         section_to_tables[current_section].append({"page": element['Page'] + 1, "path": current_path, "caption": caption})


    ############################

    return section_to_metadata, page_to_text, section_to_figures, section_to_tables




########################

#@click.command()
#@click.argument("extract_path", type=Path)
def extract_metadata(
        extract_path: Path
):
    #with extract_path.open() as fp:
    with open(extract_path) as fp:
        extract = json.load(fp)

    tree, page_to_text, section_to_figures, section_to_tables = extract_to_tree_v4(extract['elements'])
    
    metadata = {"pages": [],
                "sections": []}#,
                #"figures":  [],
                #"tables": []}
    
    for key in tree.keys():
        metadata["pages"] = page_to_text
        metadata["sections"].append({
            "title": tree[key]['title'],
            "pages": tree[key]['pages'],
            "text": tree[key]['text']
        })
        #if key in section_to_figures:
        #    for fig in section_to_figures[key]:
        #        metadata["figures"].append(fig)
        #if key in section_to_tables:
        #    for tab in section_to_tables[key]:
        #        metadata["tables"].append(tab)

    #print(json.dumps(metadata, indent=2))
    return metadata

    #metadata = {   
    #    'sections': tree.sections
    #}
    #
    #print(tree)
    #print("Start of metadata")
    #print(json.dumps(metadata, indent=2))
    #print(metadata)
    #return metadata

if __name__ == '__main__':

    from os import listdir
    from os.path import isfile, join
    import json
    folder_path = "data/valid_json/"
    metadata_path = "data/valid_metadata/"
    valid_jsons = [f for f in listdir(folder_path) if isfile(join(folder_path, f))]
    #str_path = "Archive/fetched/1/DR--1079341.json"
    #valid_jsons = ['DR--1058108.json']
    for json_file in valid_jsons:
        testing_file_path = Path(folder_path + json_file)
        print(testing_file_path)
        current_metadata = extract_metadata(testing_file_path)
        with open(metadata_path + json_file.replace(".json", "-metadata.json"), 'w') as f:
            json.dump(current_metadata, f, indent=2)
