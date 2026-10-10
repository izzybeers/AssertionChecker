
import pandas as pd
import numpy as np
import re
import os
import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
api_key = os.environ.get('OPENAI_API_KEY')
client = OpenAI(api_key = api_key)

def get_neighboring_pages(source_id, rows, index):
    source_rows = [p for p in rows if p['source_id'] == source_id]
    this_page = next((p for p in source_rows if p['page_index'] == index), None)
    previous_page = next((p for p in source_rows if p['page_index'] == index - 1), None) if index > 0 else None
    next_page = next((p for p in source_rows if p['page_index'] == index + 1), None) if index < len(source_rows) - 1 else None
    return this_page, previous_page, next_page

def page_number_context(page_text, n_chars=1000):
    if page_text is None:
        return None
    if len(page_text) <= n_chars * 2:
        return page_text
    return (
        page_text[:n_chars]
        + "\n\n[... middle of page omitted ...]\n\n"
        + page_text[-n_chars:]
    )

def get_strange_page_numbers(page_rows, source_id):
    return [
        p for p in page_rows
        if (p['source_id'] == source_id)
        and (((p['page_index'] > 0)
        and (p['page_index'] < len([x for x in page_rows if x['source_id'] == source_id]) - 1)
        and pd.notna(p['page_display_number'])
        and (prev_display := next(
                (x['page_display_number']
                for x in page_rows
                if (x['source_id'] == source_id)
                and (x['page_index'] == p['page_index'] - 1)
                and pd.notna(x['page_display_number'])),
                None
            )
        ) is not None
        and (next_display := next(
                (x['page_display_number']
                for x in page_rows
                if (x['source_id'] == source_id)
                and (x['page_index'] == p['page_index'] + 1)
                and pd.notna(x['page_display_number'])),
                None)) is not None
        and str(prev_display).isdigit()
        and str(next_display).isdigit()
        and str(p['page_display_number']).isdigit()
        and (int(prev_display) == int(next_display) - 2)
        and (int(p['page_display_number']) != int(prev_display) + 1))
        or (
            (p['page_index'] == 0)
            and (p['page_display_number'] != "1")
            and (next_display := next(
                (x['page_display_number']
                for x in page_rows
                if (x['source_id'] == source_id)
                and (x['page_index'] == p['page_index'] + 1)
                and pd.notna(x['page_display_number'])
                and x['page_display_number'] == "2"),
                None)) is not None
                
        )
        or (
                (p['page_index'] == len([
                    x for x in page_rows
                    if x['source_id'] == source_id
                ]) - 1)
                and pd.notna(p['page_display_number'])
                and (prev_display := next(
                    (
                        x['page_display_number']
                        for x in page_rows
                        if (x['source_id'] == source_id)
                        and (x['page_index'] == p['page_index'] - 1)
                        and pd.notna(x['page_display_number'])
                    ),
                    None
                )) is not None
                and str(p['page_display_number']).isdigit()
                and str(prev_display).isdigit()
                and (
                    int(p['page_display_number'])
                    != int(prev_display) + 1
                )
            )
        )
    ]

def llm_page_number_verification(list_of_pages_to_verify):
    count = 1
    print("Verifying ambiguous page number displays with LLM...")
    for page in list_of_pages_to_verify:
        print(f"Running {count} of {len(list_of_pages_to_verify)}: {page['source_id']} page index {page['page_index']}")
        has_previous = False
        has_next = False
        page_text = page_number_context(page['this_page']['page_raw_text'])
        if page['previous_page'] is not None:
             previous_page_text = page_number_context(page['previous_page']['page_raw_text'])
             has_previous = True
        if page['next_page'] is not None:
             next_page_text = page_number_context(page['next_page']['page_raw_text'])
             has_next = True

        if has_previous and has_next:
             prompt_intro = 'In the context of the previous page and the next page,'
             prompt_ending = f"Previous page: {previous_page_text}. Next page: {next_page_text}."
        elif has_previous:
             prompt_intro = 'This is the final page of the document excerpt. In the context of the previous page,'
             prompt_ending = f"Previous page: {previous_page_text}."
        elif has_next:
             prompt_intro = 'This is the first page of the document excerpt. In the context of the next page,'
             prompt_ending = f"Next page: {next_page_text},"
        else:
             prompt_intro = 'This is the only page of the document excerpt.'
             prompt_ending = ''
        
        prompt = (
            f"{prompt_intro} review the current page and identify the document's "
            "display page number. "

            "The display page number is the number used to number the pages of this "
            "PDF/document itself, typically appearing in a recurring header or footer. "

            "Do NOT return internal legal reporter pagination, star pagination, "
            "case reporter page numbers, citation numbers, footnote numbers, section "
            "numbers, dates, years, or other numbers appearing in the body text. "
            "For example, reporter markers such as '*949' or '*175' are NOT "
            "display page numbers. "

            "Use the previous and next pages to identify the document's recurring "
            "header/footer pagination pattern. Then inspect the beginning and end of "
            "the current page for a number appearing in that same kind of pattern. "

            "Before returning your answer, silently verify it a second time against "
            "the current page's header/footer context and the neighboring pages. "

            "IMPORTANT: Before returning null, verify that there truly is no document "
            "display page number anywhere in the current page's header or footer "
            "context. If there is a standalone number associated with the recurring "
            "header/footer pattern, return that number even if the page also contains "
            "many other competing numbers. "

            "Use numerical sequence only as a consistency check. Do NOT infer a page "
            "number solely because the previous and next pages suggest what the number "
            "should be. The number must actually appear on the current page. "

            "Set page_display_number to the displayed document page number. "
            "Set page_display_number to null only if the current page genuinely has "
            "no displayed document page number. "

            f"Current page header/footer context: {page_text}. "
            f"{prompt_ending}"
        )
        response = client.responses.create(
                model = 'gpt-5',
                input = prompt,
                text = {
                    'format': {
                        'type': 'json_schema',
                        'name': 'page_display_number',
                        'strict': True,
                        'schema': {
                                'type': 'object',
                                'properties': {
                                    "page_display_number": {
                                        "type": ["string", "null"],
                                        "description": "The page number visibly used to number the current PDF/document page, "
                                                        "usually in a recurring header or footer. Exclude reporter pagination, "
                                                        "star pagination, citations, dates, years, footnotes, and body-text "
                                                        "numbers. Return null only after verifying that no document display page "
                                                        "number appears in the current page's header/footer context."
                                    }
                                },
                                "additionalProperties": False,
                                "required": ['page_display_number']
                        }
                    }
                }
            )

        response_text = json.loads(response.output_text)
        page['llm_page_display_number'] = response_text['page_display_number']
        if page['llm_page_display_number'] == page['this_page']['page_display_number']:
            print("LLM confirms original assessment.")
        else:
            print(f"LLM changing display page number from {page['this_page']['page_display_number']} to {page['llm_page_display_number']}")
        count = count+1

    return list_of_pages_to_verify

def pincite_to_set(pincite):
    if pincite is None or pd.isna(pincite):
        return set()

    pages = set()

    for part in str(pincite).split(','):
        part = part.strip()

        if '-' in part:
            start, end = part.split('-', 1)
            pages.update(range(int(start), int(end) + 1))
        else:
            pages.add(int(part))

    return pages


def ClassifyAssertionSupport(statement, chunk_list, local = True):

    prompt = f"""
        Act as an assertion checker assigned with reviewing an author's citations and making sure that the author's assertions are correctly supported by the sources.
        Consider the following statement: {statement}.

        The goal is to identify the passage or passages that the author was referring to and determine whether the relevant source material supports the statement, contradicts the statement, is insufficient, or contains no match.

        Evaluate each material part of the assertion separately. When the applicable evidence rules permit reliance on multiple passages, evaluate those passages together to determine whether all material parts of the author's assertion are supported.

        If the relevant evidence supports some material parts but not others, classify it as Insufficient. When explaining an Insufficient result, identify specifically which parts are supported and which parts are not supported; do not describe a proposition as unsupported if another properly selected passage establishes it.

        When identifying what is unsupported, use only the factual requirements actually stated by the author. Do not add a broader scope, frequency, generality, or additional examples that the author's statement does not require. For example, if the statement says 'including X,' evidence establishing X can satisfy that example; do not require evidence of additional examples unless the statement expressly does so.

        Fill in the properties as JSON.
     """
    if local:
        evidence_instruction = """
        The provided chunks all come from the location cited by the author.

        You may rely on multiple non-contiguous passages when the author's
        assertion contains multiple material propositions and different passages
        within the cited location support different propositions.

        Use the minimum number of passages necessary. Do not combine passages
        unless each one directly supports or contradicts a material part of the
        author's assertion.

        You may also use multiple chunks when a single continuous passage has
        been split across chunk boundaries.
        """
        chunk_id_instruction = "The chunk ID or IDs containing the passage relied upon."
        passage_text_instructions = """
            The source passage or passages relied upon.

            If multiple selected chunks contain one continuous passage that was merely
            split by chunk boundaries, combine the relevant language normally without
            an ellipsis.

            If the selected evidence consists of separate non-contiguous passages,
            include the relevant language from each passage and place ' [...] ' between
            them.

            Use only the portions of each passage relevant to the author's assertion.
            """
    else:
        evidence_instruction = """
            The provided chunks were retrieved from across the source.

            Normally select one coherent passage. You may return multiple chunk IDs
            only when they contain a single continuous passage or immediately
            continuing discussion that has been split across chunk boundaries.
            Do not combine disconnected passages from different locations in the
            source merely because together they would support the author's assertion.

            For sourcewide review, select the strongest coherent passage that most
            directly bears on the assertion, regardless of whether it is at the
            author's cited location or elsewhere in the source. Do not prefer a
            different location merely because it is different from the author's
            citation. If two passages are comparably strong, either may be selected.
            The primary purpose of sourcewide review is to determine whether the
            author's cited location is substantively correct; identifying additional
            supporting or contradictory passages elsewhere is useful but secondary.
            """
        chunk_id_instruction = """
            The chunk ID or IDs containing the passage relied upon.
            Normally return exactly one chunk ID. Return multiple chunk IDs only when
            the relevant evidence forms one continuous passage or thought that crosses
            a chunk boundary and the chunks are contiguous in the source. Do not
            combine non-contiguous chunks merely because they separately contain
            evidence relevant to the statement. Do not combine unrelated passages
            from different parts of the source.
            """

        passage_text_instructions = "The source passage relied upon."
    #which chunk id 
    response = client.responses.create(
        model = 'gpt-5',
        instructions = prompt + evidence_instruction,
        input = json.dumps(chunk_list, ensure_ascii = False),
        text = {
            'format': {
                'type': 'json_schema',
                'name': 'assertion_support',
                'strict': True,
                'schema': {
                        'type': 'object',
                        'properties': {
                            "assertion_conclusion": {
                                "type": "string",
                                "enum": ["Supports", "Contradicts", "Insufficient", "No Match"],
                                "description": (
                                    "Possible values: Supports, Contradicts, Insufficient, No Match. "
                                    "Put Supports only if the passage supports all material parts of the writer's statement. "
                                    "If the statement contains multiple factual propositions, including propositions joined by words such as 'and,' "
                                    "the passage must support each material proposition for the conclusion to be Supports. "
                                    "Do not treat support for only part of the statement as support for the entire statement, and do not infer "
                                    "specific facts that the passage does not state or reasonably establish. "
                                    "Do not interpret a general noun phrase as asserting that every possible member of that category "
                                    "has the stated characteristic unless the author uses universal language such as 'all,' 'every,' or "
                                    "'each,' or the context otherwise clearly requires that reading. "
                                    "Distinguish CONTRADICTS, INSUFFICIENT, and NO MATCH carefully. "

                                    "Classify as CONTRADICTS only when the passage affirmatively establishes "
                                    "that a material proposition in the author's assertion is false or materially "
                                    "incompatible with the source. "
                                    "Merely discussing a different issue, failing to mention the assertion, "
                                    "or containing information on the same general subject does not contradict the assertion. "

                                    "Classify as INSUFFICIENT when the passage is genuinely relevant to the author's "
                                    "assertion but does not establish all of its material propositions. This includes when "
                                    "the passage establishes only part of the assertion, uses materially narrower language, "
                                    "or leaves a material proposition uncertain. "

                                    "Classify as NO MATCH when the passage does not actually address the proposition "
                                    "the author is asserting, even if it concerns the same case, parties, events, or general subject matter. "

                                    "Do not classify a passage as CONTRADICTS merely because the author's assertion "
                                    "goes beyond what the source proves. CONTRADICTS requires affirmative evidence "
                                    "against the assertion, not merely missing support. "

                                    "When a passage contains both evidence favoring the assertion and evidence "
                                    "materially inconsistent with an unqualified or broader assertion, evaluate "
                                    "the passage as a whole. Do not classify the passage as Supports merely because "
                                    "one sentence supports a narrower version of the assertion if another sentence "
                                    "affirmatively undermines the assertion as actually written. "

                                    "Do not infer a contradiction from the fact that the source discusses or resolves "
                                    "a different claim, issue, legal theory, remedy, or procedural question. "
                                    "To classify as Contradicts, the passage must affirmatively address a material "
                                    "proposition in the assertion and establish something incompatible with it. "

                                    "For sourcewide review, select the strongest coherent passage that most directly "
                                    "bears on the assertion, regardless of whether it is at the author's cited location "
                                    "or elsewhere in the source. Do not prefer a different location merely because it "
                                    "is different from the author's citation. If two passages are comparably strong, "
                                    "either may be selected. The primary purpose of sourcewide review is to determine "
                                    "whether the author's cited location is substantively correct; identifying additional "
                                    "supporting or contradictory passages elsewhere is useful but secondary."
                                )
                            },
                            "chunk_ids": {
                                "type": ["array"],
                                "items": {"type": "string"},
                                "description": chunk_id_instruction
                            },
                            "passage_text": {
                                "type": ["string", "null"],
                                "description": passage_text_instructions
                            },
                            # "is_exact_quote": {
                            #     "type": "boolean",
                            #     "description": "True if the author's assertion involves an exact quote. False if it does not."
                            # },
                            # "exact_quote_match": {
                            #     "type": ["boolean", "null"],
                            #     "description": "If the statement is not a direct quote of the source, put None. if it is a direct quote, put True if the direct quote matches exactly in the source text, and False if not."
                            # },
                            "explanation": {
                                "type": "string",
                                "description": (
                                    "Explain the reasoning for the conclusion you reached, as if you were speaking to the author and instructing as to why you classified their assessment as you did."
                                    "If you found the statement supported the chunks, write one sentence explaining why it supports."
                                    "If you found the statement contradicted the chunks, write 1-2 sentences explaining what was contradictory about it."
                                    "If you found the passage insufficient, write 1-2 sentences identifying which material parts of the author's statement the passage supports and which material parts it does not support. Be precise and clause-specific. Do not say that a fact is missing if the passage actually establishes that fact. Explain only the additional information or inference needed to support the full statement."
                                    "If you found the statement did not refer to anything in the passages, state this briefly."
                                    # "If it was a direct quote and it matched, state briefly that the quote matched."
                                    # "If it was a direct quote and it did not match, provide what is different about the passage's quote. The source is the truth, so explain changes from the point of view of the writer's statement. What needs to be changed from the writer's statement to make it match? If you do not think it matches, double check that it does not match before returning."
                                    "Do not refer to chunk ids in this explanation. This is a plain-English explanation to a non-technical writer."

                                )
                            }
                        },
                        "additionalProperties": False,
                        "required": ['assertion_conclusion', 'chunk_ids', 'passage_text', 'explanation']
                }
            }
        }
    )

    assertion_support = json.loads(response.output_text)
    assertion_support['is_exact_quote'] = False
    assertion_support['exact_quote_match'] = None
    selected_chunk_ids = assertion_support['chunk_ids']
    corresponding_pincites = sorted(set(int(c['pincite']) for c in chunk_list if c['chunk_id'] in selected_chunk_ids and c['pincite'] is not None and str(c['pincite']) != 'None'))
    if len(corresponding_pincites) == 0:
        corresponding_pincite = None
    elif len(corresponding_pincites) == 1:
        corresponding_pincite = str(corresponding_pincites[0])
    elif corresponding_pincites == list(range(corresponding_pincites[0], corresponding_pincites[-1] + 1)):
        corresponding_pincite = f"{corresponding_pincites[0]}-{corresponding_pincites[-1]}"
    else:
        pincite_string = str(corresponding_pincites[0])
        latest_pincite = int(corresponding_pincites[0])
        current_sequence = [int(corresponding_pincites[0])]
        for p in corresponding_pincites[1:]:
            if int(p) == latest_pincite + 1 and p != corresponding_pincites[-1]: #consecutive from the previous one
                current_sequence.append(int(p))
                latest_pincite = int(p)
            elif len(current_sequence) > 1 and int(p) != latest_pincite + 1: #just completed a sequence but still have more left
                pincite_string += ('-' + str(max(current_sequence))) + ', ' + str(p)
                latest_pincite = p
                current_sequence = [int(p)]
            elif int(p) == latest_pincite + 1 and p == corresponding_pincites[-1]: #in a sequence but at the end of pincite
                pincite_string += ('-' + str(p))
            else: #only one number in current_sequence
                pincite_string += ', ' + str(p)
                latest_pincite = p
                current_sequence = [int(p)]

        corresponding_pincite = pincite_string
    assertion_support['pincite'] = corresponding_pincite
    return pd.DataFrame([assertion_support])


def create_chunks(pages, blocks, chunk_size_paragraphs = 1, overlapping_paragraphs = 1):

    child_chunks = []
    parent_chunks = []
    for source in np.unique([p['source_id'] for p in pages]):
        for page_index in np.unique([p['page_index'] for p in [p for p in pages if p['source_id'] == source]]):
            this_page = [p for p in pages if p['page_index'] == page_index and p['source_id'] == source][0]
            blocks_this_page = [b for b in blocks if b['page_index'] == page_index and b['source_id'] == source]
            #tables_this_page = [t for t in tables if t['page_index'] == page_index and t['source_id'] == source]

            #parent chunk:
            parent_chunk_text = ''
            if page_index > 0:
                previous_page = [p for p in pages if p['page_index'] == (page_index-1) and p['source_id'] == source]
                parent_chunk_text += previous_page[0]['page_raw_text']
                #tables_previous_page = [t for t in tables if t['page_index'] == (page_index-1) and t['source_id'] == source]
                # if len(tables_previous_page) > 0:
                #     parent_chunk_text += '\n\n' + str(tables_previous_page[0]['table_text'])

            parent_chunk_text += this_page['page_raw_text']
            # if len(tables_this_page) > 0:
            #     parent_chunk_text += "\n\n" + str(tables_this_page[0]["table_text"])

            next_page = [p for p in pages if p['page_index'] == (page_index+1) and p['source_id'] == source]
            if next_page:
                parent_chunk_text += next_page[0]['page_raw_text']
                #tables_next_page = [t for t in tables if t['page_index'] == (page_index+1) and t['source_id'] == source]
                # if len(tables_next_page) > 0:
                #     parent_chunk_text += '\n\n' + str(tables_next_page[0]['table_text'])

            parent_chunks.append({
                'chunk_id': str(source) + 'page' + str(page_index),
                'source_id': source,
                'page_index': page_index,
                'pdf_page_number': this_page['pdf_page_number'],
                'page_display': this_page['page_display_number'],
                'chunk_text': parent_chunk_text
            })
            paragraphs = [{'text': block["block_text"].strip(), 'pincite': block['pincite']} for block in blocks_this_page if block["block_type"] == "text" and block["block_text"].strip()]
            paragraphs = [{**p, 'text': re.sub(r"(?<=\w)-\s*\n\s*(?=\w)", "", p['text'])} for p in paragraphs]
            paragraphs = [{**p, 'text': re.sub(r"\s*\n\s*", " ", p['text'])} for p in paragraphs]
            
            for i in range(len(paragraphs)):
                start = max((i-overlapping_paragraphs),0)
                end = (min((i+overlapping_paragraphs),len(paragraphs)) + chunk_size_paragraphs)
                child_chunk_text = ' '.join(p['text'] for p in paragraphs[start:end] if str(p['pincite']) == str(paragraphs[i]['pincite']))
                child_chunks.append({
                    'chunk_id': str(source) + 'page' + str(page_index) + 'paragraph' + str(i),
                    'source_id': str(source),
                    'page_index': int(page_index),
                    'pdf_page_number': this_page['pdf_page_number'],
                    'page_display': this_page['page_display_number'],
                    'chunk_text': child_chunk_text,
                    'pincite': paragraphs[i]['pincite'],
                    'parent_chunk_id': str(source) + 'page' + str(page_index)
                })

    return [child_chunks, parent_chunks]


def process_citation(source, pincite, statement, child_chunks, parent_chunks, retrievers):

    # source_parent_chunks = [{'chunk_id': str(p['chunk_id']),
    #                          'chunk_text': str(p['chunk_text'])} for p in parent_chunks if p['source_id'] == source]

    statement_clean = statement.strip()
    is_exact_quote = (statement_clean.startswith('"') and statement_clean.endswith('"'))  or (statement_clean.startswith('“') and statement_clean.endswith('”'))
    if is_exact_quote:
        quote_text = re.sub(r'\s+', ' ', statement_clean[1:-1]).strip()

    source_child_chunks = [{'chunk_id': str(c['chunk_id']),
                            'chunk_text': str(c['chunk_text']),
                            'pincite': str(c['pincite']),
                            'parent_chunk_id': c['parent_chunk_id']}
                            #'parent_chunk_text': [p['chunk_text'] for p in source_parent_chunks if p['chunk_id'] == c['parent_chunk_id']]
                            for c in child_chunks if c['source_id'] == source]

    #local check:
    if pincite is not None:
        if '-' in pincite and ',' not in pincite:
            pincites_upper_lower = pincite.split('-')
            if len(pincites_upper_lower) > 1:
                pincites = [str(i) for i in range(int(pincites_upper_lower[0]), int(pincites_upper_lower[-1]) + 1)]
            else:
                pincites = pincites_upper_lower
        elif ',' in pincite and '-' not in pincite:
            pincites = [p.strip() for p in pincite.split(',')]
        elif '-' in pincite and ',' in pincite:
            pincite_list = []
            pincite_comma_pieces = [p.strip() for p in pincite.split(',')]
            for p in pincite_comma_pieces:
                if '-' in p:
                    upper_lower = p.split('-')
                    pincite_list.extend([str(i) for i in range(int(upper_lower[0]), int(upper_lower[-1]) + 1)])
                else:
                    pincite_list.append(p)
            pincites = pincite_list
        else:
            pincites = [str(pincite)]
        if not is_exact_quote:
            child_chunks_this_pincite = [c for c in source_child_chunks if str(c['pincite']) in pincites]
            child_chunks_to_use = set()
            for retriever in retrievers:
                new_child_chunks = retriever.retrieve(statement, child_chunks_this_pincite, min(len(child_chunks_this_pincite), 20))
                child_chunks_to_use.update(pd.concat(new_child_chunks, axis=0).query('score_metric=="cosine_only"')['chunk_id'])
            local_conclusion = ClassifyAssertionSupport(statement, [c for c in child_chunks_this_pincite if c['chunk_id'] in child_chunks_to_use]).add_prefix('local_')
        else:
            chunks_with_quote = [c for c in source_child_chunks if str(c['pincite']) in pincites and quote_text in re.sub(r'\s+', ' ', c['chunk_text']).strip()]
            if len(chunks_with_quote) > 0:
                matched_chunk = chunks_with_quote[0]
                pincites = list(sorted(set([int(c['pincite']) for c in chunks_with_quote])))
                min_pincite = pincites[0]
                max_pincite = pincites[-1]
                local_conclusion = pd.DataFrame({
                    'local_assertion_conclusion': [None],
                    'local_chunk_ids': [','.join(set([c['chunk_id'] for c in chunks_with_quote]))],
                    'local_passage_text': [quote_text],
                    'local_is_exact_quote': [True],
                    'local_exact_quote_match': [True],
                    'local_explanation': [None],
                    'local_pincite': [min_pincite if min_pincite == max_pincite else str(min_pincite) + '-' + str(max_pincite)]
                })
            else:
                local_conclusion = pd.DataFrame({
                    'local_assertion_conclusion': [None],
                    'local_chunk_ids': [None],
                    'local_passage_text': [None],
                    'local_is_exact_quote': [True],
                    'local_exact_quote_match': [False],
                    'local_explanation': [None],
                    'local_pincite': [pincite]
                })
    else: #citing source generally, no pincite
        local_conclusion = pd.DataFrame({
            'local_assertion_conclusion': [None],
            'local_chunk_ids': [None],
            'local_passage_text': [None],
            'local_is_exact_quote': [None],
            'local_exact_quote_match': [None],
            'local_explanation': [None],
            'local_pincite': [None]
        })

    #sourcewide check:

    if not is_exact_quote:      
        chunks_for_assertion = set()
        for retriever in retrievers:
            new_chunks_for_assertion = retriever.retrieve(statement, source_child_chunks, min(len(source_child_chunks), 20))
            chunks_for_assertion.update(pd.concat(new_chunks_for_assertion, axis=0).query('score_metric=="cosine_only"')['chunk_id'])
        # chunks_for_support_of_assertion = retriever.get_top_chunks(min(len(source_child_chunks), 20), 'Find passages that support the following statement: ' + statement, source_child_chunks, False, parent_chunks)
        # chunks_for_contradiction_of_assertion = retriever.get_top_chunks(min(len(source_child_chunks), 20), 'Find passages that contradict the following statement: ' + statement, source_child_chunks, False, parent_chunks)
        
        sourcewide_conclusion = ClassifyAssertionSupport(statement, [c for c in source_child_chunks if c['chunk_id'] in chunks_for_assertion], local = False).add_prefix('sourcewide_')
    else:
        chunks_with_quote = [c for c in source_child_chunks if quote_text in re.sub(r'\s+', ' ', c['chunk_text']).strip()]
        if len(chunks_with_quote) > 0:
            matched_chunk = chunks_with_quote[0]
            sourcewide_conclusion = pd.DataFrame({
                'sourcewide_assertion_conclusion': [None],
                'sourcewide_chunk_ids': [matched_chunk['chunk_id']],
                'sourcewide_passage_text': quote_text,
                'sourcewide_is_exact_quote': [True],
                'sourcewide_exact_quote_match': [True],
                'sourcewide_explanation': [None],
                'sourcewide_pincite': [matched_chunk['pincite']]
            })
        else:
            sourcewide_conclusion = pd.DataFrame({
                'sourcewide_assertion_conclusion': [None],
                'sourcewide_chunk_ids': [None],
                'sourcewide_passage_text': [None],
                'sourcewide_is_exact_quote': [True],
                'sourcewide_exact_quote_match': [False],
                'sourcewide_explanation': [None],
                'sourcewide_pincite': [None]
        })
            
    full_conclusion = pd.concat([local_conclusion, sourcewide_conclusion], axis = 1)
    full_conclusion = full_conclusion.assign(
                                             cited_pincite = pincite,
                                             min_local_pincite = lambda x: x['local_pincite'].astype('string').str.split('-').str[0],
                                             max_local_pincite = lambda x: x['local_pincite'].astype('string').str.split('-').str[-1],
                                             min_sourcewide_pincite = lambda x: x['sourcewide_pincite'].astype('string').str.split('-').str[0],
                                             max_sourcewide_pincite = lambda x: x['sourcewide_pincite'].astype('string').str.split('-').str[-1],
                                             final_assertion_assessment = lambda x:
                                             np.select(
                                                 condlist=[
                                                    x['local_is_exact_quote'].eq(True) & x['local_exact_quote_match'].eq(True) & x['cited_pincite'].notna(),
                                                    x['local_is_exact_quote'].eq(True) & x['local_exact_quote_match'].eq(False) & x['sourcewide_exact_quote_match'].eq(True)  & x['cited_pincite'].notna(),
                                                    x['local_is_exact_quote'].eq(True) & x['local_exact_quote_match'].eq(False) & x['sourcewide_exact_quote_match'].eq(False)  & x['cited_pincite'].notna(),
                                                    x['sourcewide_is_exact_quote'].eq(True) & x['sourcewide_exact_quote_match'].eq(True)  & x['cited_pincite'].isna(),
                                                    x['sourcewide_is_exact_quote'].eq(True) & x['sourcewide_exact_quote_match'].eq(False)  & x['cited_pincite'].isna(),
                                                    x['cited_pincite'].isna(),
                                                    (x['local_assertion_conclusion'] == x['sourcewide_assertion_conclusion'])
                                                    & (x['local_assertion_conclusion'] == 'No Match'),
                                                    (x['local_assertion_conclusion'] == 'Insufficient') & x['sourcewide_assertion_conclusion'].isin(['Insufficient', 'No Match']),
                                                    (x['local_assertion_conclusion'] == 'No Match') & (x['sourcewide_assertion_conclusion'] == 'Insufficient'),
                                                    ((x['local_assertion_conclusion'] == x['sourcewide_assertion_conclusion']) & x.apply(lambda row:pincite_to_set(row['sourcewide_pincite']).issubset(pincite_to_set(row['cited_pincite'])) and len(pincite_to_set(row['sourcewide_pincite'])) > 0, axis=1)),
                                                    x['local_assertion_conclusion'].isin(['Insufficient', 'No Match']) & x['sourcewide_assertion_conclusion'].isin(['Supports', 'Contradicts']),
                                                    (x['local_assertion_conclusion'] == 'Contradicts') & (x['sourcewide_assertion_conclusion'] == 'Supports'),
                                                    (x['local_assertion_conclusion'] == 'Supports') & (x['sourcewide_assertion_conclusion'] == 'Contradicts'),
                                                    x['local_assertion_conclusion'].isin(['Supports', 'Contradicts']) & x['sourcewide_assertion_conclusion'].isin(['Insufficient', 'No Match']),
                                                    x['local_assertion_conclusion'] == x['sourcewide_assertion_conclusion']
                                                ],
                                                 choicelist= [
                                                     'Exact Quote Match',
                                                     'Exact Quote Match In Other Location',
                                                     'Exact Quote Mismatch',
                                                     'Exact Quote Match, No Pincite',
                                                     'Exact Quote Mismatch, No Pincite',
                                                     'General Citation: ' + x['sourcewide_assertion_conclusion'].astype('object').fillna(''),
                                                     'No Match Anywhere',
                                                     'Insufficient With No Better Location',
                                                     'No Match At Cited Location, Insufficient in Alternate Location',
                                                     x['local_assertion_conclusion'].astype('object').fillna('') + ' At Cited Location',
                                                     x['local_assertion_conclusion'].astype('object').fillna('') + ' At Cited Location, ' + x['sourcewide_assertion_conclusion'].astype('object').fillna('') + " in Alternate Location",
                                                     "Current Location Contradicts, Supports Elsewhere",
                                                    "Supports At Pincite, Contradicted Elsewhere",
                                                    x['local_assertion_conclusion'].astype('object').fillna('') + ' At Cited Location',
                                                     x['local_assertion_conclusion'].astype('object').fillna('') + ", 2 Different Locations"
                                                 ],
                                                 default = 'Other'
                                             ),
                                             statement = statement,
                                             source_id = source
                                             ).drop(columns = ['min_local_pincite', 'max_local_pincite', 'min_sourcewide_pincite', 'max_sourcewide_pincite'])
    return full_conclusion[['source_id', 'cited_pincite', 'statement', 'final_assertion_assessment',
                            'local_pincite', 'local_chunk_ids', 'local_passage_text', 'local_assertion_conclusion', 'local_is_exact_quote', 'local_exact_quote_match', 'local_explanation',
                            'sourcewide_pincite', 'sourcewide_chunk_ids', 'sourcewide_passage_text', 'sourcewide_assertion_conclusion', 'sourcewide_is_exact_quote', 'sourcewide_exact_quote_match', 'sourcewide_explanation']]


def llm_extract_citations(text, previous_text, paragraph_number):
    if len(text.strip()) == 0:
        return []
    print("Calling LLM...")
    response = client.responses.create(
        model = 'gpt-5',
        instructions = ("Identify every source citation in the provided text that is being used as authority "
                        "or evidence for a factual or legal assertion. "
                        "Return the exact text of each cited authority as it appears, excluding citation signals "
                        "and citation relationship words as described below. "
                        
                        "Extract citations only from the Text to analyze. "
                        "The previous paragraph is provided only as context for determining what a citation supports. "
                        "Do not return citations that appear only in the previous paragraph. "

                        "For citation_source, return the portion of the citation that identifies the source itself, "
                        "with the pinpoint locator removed but all other identifying citation information preserved. "

                        "Do NOT treat every mention of a statute, regulation, case, document, or other source as a citation. "
                        "A source reference is a citation for this task only when it functions as attribution, authority, "
                        "or evidentiary support for a statement. If a statute, regulation, case, or document is itself the "
                        "subject of the sentence or is mentioned as part of the substantive proposition, do not extract it "
                        "merely because it resembles a citation. "

                        "However, a statute, regulation, case, or other source reference SHOULD be extracted when it "
                        "functions as attribution for quoted or paraphrased source language. In particular, extract a "
                        "source citation that appears parenthetically after quoted language or appears immediately after "
                        "a block quotation to identify the source of that quotation. This is true even if the same statute "
                        "or regulation is also discussed by name in the surrounding substantive text. "

                        "For example, in 'Labor Law § 241(6) provides ... “reasonable and adequate protection” "
                        "(Lab Law § 241 [6])', do not extract the first mention of 'Labor Law § 241(6)' merely because "
                        "it is the subject of the sentence, but DO extract 'Lab Law § 241 [6]' because it attributes the "
                        "quoted statutory language. Likewise, when a block quotation is followed by "
                        "'12 NYCRR § 23–1.16 [b]', extract that citation because it identifies the source of the quotation. "

                        "For example, in 'Industrial Code § 23-1.16(b) is sufficiently specific ... "
                        "(Yaucan, 155 AD3d at 926)', extract 'Yaucan, 155 AD3d at 926' but not "
                        "'Industrial Code § 23-1.16(b)'. "

                        "If one citation parenthetical contains multiple authorities, identify each citation separately. "
                        "For example, in '(Yaucan, 155 AD3d at 926, quoting Anderson v MSG Holdings, L.P., "
                        "146 AD3d 401, 404 [1st Dept 2017])', return Yaucan and Anderson as separate citations. "

                        "Classify abbreviated citations that depend on earlier context to identify the source as "
                        "'short form'. This includes Id., supra citations, shortened case citations, deposition "
                        "references such as 'Michaels EBT at 122', and similar abbreviated citations. "

                        "For each citation, identify the statement or statements that the citation appears intended "
                        "to support. Preserve the wording of those statements from the provided text. "
                        
                        "If the text contains no citations, return an empty citations array. "
                        "Do not return explanatory text, requests for more input, placeholders, "
                        "or statements saying that no citations were found. "
                        
                        "Do not include citation signals such as 'See' or 'see e.g.' in citation_text. "
                        "Return them separately as citation_signal. "

                        "When one cited authority is introduced through a relationship to another cited authority, "
                        "such as 'citing' or 'quoting', return each authority as a separate citation ."
                        "Do not include 'citing' or 'quoting' in citation_text. Instead, put that relationship "
                        "in citation_relationship for the authority that follows the relationship word. "
                        "Preserve the citations in the order in which they appear in the text. "),
        input = f"Text to analyze: {text}\nPrevious paragraph for context only: {previous_text}",
        text = {
                'format': {
                    'type': 'json_schema',
                    'name': 'citations',
                    'strict': True,
                    'schema': {
                            'type': 'object',
                            'properties': {
                                'citations': {
                                    'type': 'array',
                                    'items': {
                                        'type': 'object',
                                        'properties': {
                                            "citation_text": {
                                                "type": ["string"],
                                                "description": "Full text of the citation."
                                            },
                                            'citation_source': {
                                                'type': 'string',
                                                'description': (
                                                    "The citation identifying the source itself, with the pinpoint locator removed. "
                                                    "Preserve information needed to identify the source, including the reporter's "
                                                    "initial page, court, and year when present. "
                                                    "Examples: for 'Ross v Smith, 81 NY2d 494, 500 [1993]', return "
                                                    "'Ross v Smith, 81 NY2d 494 [1993]'; for 'Zimmer, 65 NY2d at 521', "
                                                    "return 'Zimmer, 65 NY2d'; for 'Michaels EBT at 122', return 'Michaels EBT'."
                                                    "For Id. citations, return 'Id.' as citation_source. "
                                                    "For statutes and regulations, preserve the full provision identifier, including "
                                                    "subsections, paragraphs, and clauses such as '(6)', '[b]', '(d)', or '(1)', "
                                                    "as part of citation_source."
                                                )
                                            },
                                            "citation_type": {
                                                "type": 'string',
                                                "enum": ['full citation', 'short form'],
                                                'description':  "The type of citation: short form or full citation. "
                                                                "Use 'short form' for any citation that does not independently identify "
                                                                "the full source and instead refers to a source identifiable from context. "
                                                                "This includes Id., supra citations, shortened case citations, deposition "
                                                                "citations such as 'Michaels EBT at 122', and similar abbreviated record citations. "
                                            },
                                            "source_type": {
                                                "type": ['string', 'null'],
                                                'enum': ['case', 'statute/regulation', 'website', 'book', 'journal/article', 'record', 'other', None],
                                                'description':  "The type of source. Use null only when the source type truly cannot be determined, such as an ambiguous name or an id."
                                            },
                                            "associated_statement": {
                                                "type": ["string", "null"],
                                                "description": ("The exact statement or statements that this citation appears intended to support. "
                                                                "Preserve the wording from the provided text. If the citation supports a block quotation "
                                                                "or material in the previous paragraph, use that text when appropriate.")
                                            },
                                            "pincite": {
                                                'type': ['string', 'null'],
                                                'description': ("The specific pinpoint locator within the cited source that the author is referring to. "
                                                                "Do not treat the first page of a reporter citation as a pincite unless it is separately "
                                                                "identified as the pinpoint location. If the citation does not point to a specific location "
                                                                "within the source, put null. Preserve the pincite as written, including ranges and any "
                                                                "leading star. Examples: '500', '520–21', '106–07', '*11'." 
                                                                "For statutes and regulations, do not treat section, subsection, paragraph, or clause "
                                                                "identifiers as pincites. For example, in '12 NYCRR § 23–1.16 [b]', '[b]' is part "
                                                                "of citation_source and pincite should be null.")
                                                ,
                                            },
                                            "citation_signal": {
                                                "type": ["string", "null"],
                                                "description": (
                                                    "Any citation signal immediately associated with this citation, "
                                                    "such as 'See', 'see e.g.'. "
                                                    "Use null if there is none. Do not include this signal in citation_text."
                                                )   
                                            },
                                            "citation_relationship": {
                                                "type": ["string", "null"],
                                                "description": (
                                                    "Any citation relationship immediately associated with this citation, "
                                                    "such as 'citing' or 'quoting'. "
                                                    "Use null if there is none. Do not include this relationship in citation_text."
                                                )   
                                            }          
                                        },
                                        "additionalProperties": False,
                                        "required": ["citation_text", 'citation_source', "citation_type", "source_type", "associated_statement", "pincite", "citation_signal", "citation_relationship"]
                                    }
                                
                                }
                        },
                        "additionalProperties": False,
                        "required": ['citations']
                    }
                }
            }
    )
    new_citations = json.loads(response.output_text)['citations']
    for i, citation in enumerate(new_citations):
        citation['citation_id'] = f"{paragraph_number}_{i + 1}"
    return [
        {
            'paragraph_number': paragraph_number,
            'paragraph_text': text,
            **citation
        }
        for citation in new_citations
    ]