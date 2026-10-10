#%%

import pandas as pd
import numpy as np
from docx import Document
from zipfile import ZipFile
from lxml import etree
import re
import os
import json
from openai import OpenAI
from dotenv import load_dotenv
from helper_funs import llm_extract_citations

load_dotenv()
api_key = os.environ.get('OPENAI_API_KEY')
client = OpenAI(api_key = api_key)

def read_docx_footnotes(path):
    with ZipFile(path) as z:
        if "word/footnotes.xml" not in z.namelist():
            return []
        xml = z.read("word/footnotes.xml")
    
    root = etree.fromstring(xml)
    ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    footnotes = []
    for footnote in root.findall("w:footnote", ns):
        footnote_id = footnote.get("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}id")
        # Word reserves negative IDs for separator footnotes
        if int(footnote_id) < 2:
            continue
        text = "".join(t.text or "" for t in footnote.findall(".//w:t", ns))
        footnotes.append({"footnote_number": int(footnote_id)-1, "text": text})
    return footnotes

def find_footnote_references(path):
    with ZipFile(path) as z:
        if "word/footnotes.xml" not in z.namelist():
            return []
        xml = z.read("word/document.xml")

    root = etree.fromstring(xml)
    ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}

    results = []
    paragraphs = root.findall(".//w:body/w:p", ns)

    for paragraph_index, p in enumerate(paragraphs):
        text_parts = []
        text_parts_with_footnotes = []
        refs = []

        for child in p.iter():

            if child.tag == f"{{{ns['w']}}}t":
                text = child.text or ""
                text_parts.append(text)
                text_parts_with_footnotes.append(text)

            elif child.tag == f"{{{ns['w']}}}footnoteReference":
                xml_id = int(
                    child.get(f"{{{ns['w']}}}id")
                )

                footnote_number = xml_id - 1

                character_index = len(
                    "".join(text_parts)
                )

                refs.append({
                    "footnote_number": footnote_number,
                    "character_index": character_index
                })

                text_parts_with_footnotes.append(
                    f"[FOOTNOTE {footnote_number}]"
                )

        paragraph_text = "".join(text_parts)
        paragraph_text_with_footnotes = "".join(
            text_parts_with_footnotes
        )

        if refs:
            for r in refs:
                results.append({
                    "paragraph_index": paragraph_index,
                    "paragraph_text": paragraph_text,
                    "paragraph_text_with_footnotes": paragraph_text_with_footnotes,
                    "footnote_number": r['footnote_number'],
                    'character_index': r['character_index']
                })

    return results

file_name = "../manuscripts/PosteNoteDraft4.docx"
file_name = "../manuscripts/LaborLawMemo.docx"

doc = Document(file_name)
footnotes = read_docx_footnotes(file_name)
footnotes_df = pd.DataFrame(footnotes).rename(columns = {'text':'citation_text'})
citations = []
if len(footnotes) > 0:
    refs = find_footnote_references(file_name)
    refs_df = pd.DataFrame(refs)
    unique_paragraphs = refs_df[['paragraph_index','paragraph_text_with_footnotes']].drop_duplicates()
    for para in range(len(unique_paragraphs)):
        paragraph_index = unique_paragraphs.iloc[para]['paragraph_index']
        extracted_footnotes = re.findall(r'\[FOOTNOTE [0-9]+\]', unique_paragraphs.iloc[para]['paragraph_text_with_footnotes'])
        for f in extracted_footnotes:
            footnote_number = re.search(r'[0-9]+',f).group()
            footnote_citation_text = '(' + footnotes_df.loc[footnotes_df['footnote_number']==int(footnote_number), 'citation_text'].iloc[0].strip() + ')'
            new_text = unique_paragraphs.iloc[para]['paragraph_text_with_footnotes'].replace(f,footnote_citation_text)
            unique_paragraphs.loc[unique_paragraphs['paragraph_index'] == unique_paragraphs.iloc[para]['paragraph_index'], 'paragraph_text_with_footnotes'] = new_text
        adjusted_paragraph_text = unique_paragraphs.iloc[para]['paragraph_text_with_footnotes']
        previous_paragraph_text = (doc.paragraphs[paragraph_index - 1].text if paragraph_index > 0 else '')
        new_citations = llm_extract_citations(adjusted_paragraph_text, previous_paragraph_text, paragraph_index+1)
        citations.extend(new_citations)
else:
    count = 1
    for paragraph in doc.paragraphs:
        text = paragraph.text
        previous_text = doc.paragraphs[count - 2].text if count > 1 else ""
        print(f"Paragraph {count} of {len(doc.paragraphs)}")
        new_citations = llm_extract_citations(text, previous_text, count)
        citations.extend(new_citations)
        count+=1

citations_df = pd.DataFrame(citations)
direct_citations_df = citations_df.query('citation_relationship not in ["quoting","citing"]').reset_index(drop=True)
id_rows = np.where(direct_citations_df['citation_text'].str.contains(r'\bId\.', regex=True, na=False))[0]
for i in id_rows:
    citation_text = direct_citations_df['citation_text'].iloc[i]
    pincite = direct_citations_df['pincite'].iloc[i]
    previous_citation = direct_citations_df['citation_text'].iloc[int(i)-1]
    previous_citation_source_only = direct_citations_df['citation_source'].iloc[int(i)-1]
    previous_pincite = direct_citations_df['pincite'].iloc[int(i)-1]

    if re.fullmatch(r'Id\.?', citation_text.strip()): #just id alone (no pincite), takes previous citation as is
        new_citation_text = previous_citation
        new_pincite = previous_pincite
    else: #takes previous source but its own pincite
        new_citation_text = re.sub(r'Id\.', previous_citation_source_only, citation_text)
        new_pincite = pincite

    new_source = previous_citation_source_only
    new_source_type = direct_citations_df['source_type'].iloc[int(i)-1]
        
    direct_citations_df.loc[i, 'citation_text'] = new_citation_text
    direct_citations_df.loc[i, 'pincite'] = new_pincite
    direct_citations_df.loc[i, 'citation_source'] = new_source
    direct_citations_df.loc[i, 'source_type'] = new_source_type

direct_citations_df = direct_citations_df.rename(columns={
    'citation_text': 'resolved_citation_text',
    'pincite': 'resolved_pincite',
    'citation_source': 'resolved_citation_source',
    'source_type': 'resolved_source_type'   
})

citations_df = citations_df.merge(direct_citations_df[['citation_id'] + direct_citations_df.columns[direct_citations_df.columns.str.contains('resolved')].tolist()].query('resolved_citation_text.notna()'),
                                  on = 'citation_id', how = 'left')\
                                  [['citation_id', 'paragraph_number', 'paragraph_text',
                                    'associated_statement',
                                    'citation_text', 'resolved_citation_text',
                                    'citation_type', 'source_type', 'resolved_source_type',
                                    'citation_source', 'resolved_citation_source',
                                    'pincite', 'resolved_pincite',
                                    'citation_relationship', 'citation_signal'
                                    ]]

for col in citations_df.columns[citations_df.columns.str.contains('resolved')]:
    citations_df[col] = citations_df[col].fillna(citations_df[re.sub('resolved_','',col)])


#%%
