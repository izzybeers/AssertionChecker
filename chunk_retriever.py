from sentence_transformers import SentenceTransformer
import numpy as np
import pandas as pd
from transformers.utils import logging
logging.disable_progress_bar()
#this retriever takes a list of all chunks, along with a query, and returns the top n chunks related to that query.
class Retriever():
    def __init__(self, model_name, batch_size = 16):
        #model_name = 'Qwen/Qwen3-Embedding-0.6B'
        self.model_name = model_name
        self.batch_size = batch_size
        self.model = SentenceTransformer(model_name, trust_remote_code=True)
    # def get_top_chunks(self, n, query, chunks, get_parent = True, parent_chunks = None):

    #     texts = [c['chunk_text'] for c in chunks]
    #     document_embeddings = self.model.encode(texts, batch_size=16, normalize_embeddings=True, convert_to_numpy=True)

    #     query_embeddings = self.model.encode(query, batch_size=16, normalize_embeddings=True, convert_to_numpy=True)

    #     scores = query_embeddings @ document_embeddings.T
    #     ranked_child_chunks = np.argsort(scores.reshape(-1))[::-1]

    #     if not get_parent:
    #         return [chunks[i] for i in ranked_child_chunks[:n]]
    #     else:
    #         parent_chunks_selected = []
    #         for i in ranked_child_chunks:
    #             if len(parent_chunks_selected) >= min(len(parent_chunks), n):
    #                 break
    #             new_child_chunk = chunks[i]
    #             if new_child_chunk['parent_chunk_id'] not in parent_chunks_selected:
    #                 parent_chunks_selected.append(new_child_chunk['parent_chunk_id'])
    #         return [p for p in parent_chunks if p['chunk_id'] in parent_chunks_selected]

    def mmr(self, restrict_to_cosine_top_indices, chunk_similarities, cosine_chunks,k=5, fetch_k=20, lambda_mult=0.6):

        top_cosine_indices = pd.DataFrame(cosine_chunks).nlargest(fetch_k, "score")['index'].tolist()

        top_chunks_with_mmr = [{
            'chunk_id': cosine_chunks[top_cosine_indices[0]]['chunk_id'],
            'score': float(cosine_chunks[top_cosine_indices[0]]['score']),
            'relevance_to_selected_chunks': 0,
            'mmr_score': float(0.6*cosine_chunks[top_cosine_indices[0]]['score']),
            'index': int(cosine_chunks[top_cosine_indices[0]]['index'])
        }]

        cosine_scores = [row['score'] for row in cosine_chunks]

        for _ in range(k-1):
            indices_already_selected = [row['index'] for row in top_chunks_with_mmr]
            relevance_to_selected_chunks = chunk_similarities[indices_already_selected]
            max_relevance = relevance_to_selected_chunks.max(axis=0)
            weighted_scores = [lambda_mult*c for c in cosine_scores] - (1-lambda_mult)*max_relevance
            weighted_scores[indices_already_selected] = -np.inf
            if restrict_to_cosine_top_indices:
                weighted_scores[list(np.setdiff1d(range(len(cosine_chunks)), top_cosine_indices))] = -np.inf
            top_score_index = np.argmax(weighted_scores)
            top_score = weighted_scores[top_score_index]
            top_chunks_with_mmr.append({
                'chunk_id': cosine_chunks[top_score_index]['chunk_id'],
                'score':   float(cosine_chunks[top_score_index]['score']),
                'relevance_to_selected_chunks': float(max_relevance[top_score_index]),
                'mmr_score': float(top_score),
                'index': int(top_score_index)
            })

        return top_chunks_with_mmr


    def retrieve(self, query, chunks, k=5, fetch_k=20, additional_tuning_descriptor = ''):
        if 'Jina' in self.model_name:
            query_embeddings = self.model.encode(query, task = 'retrieval.query', prompt_name = 'retrieval_query', batch_size = self.batch_size, normalize_embeddings = True)
            text_embeddings = self.model.encode([c['chunk_text'] for c in chunks], task = 'retrieval.passage', prompt_name = 'retrieval_passage',  batch_size = self.batch_size, normalize_embeddings = True)
        elif 'e5' in self.model_name:
            chunks_altered = [{**c, 'chunk_text': 'passage: ' + c['chunk_text']} for c in chunks]
            query_embeddings = self.model.encode('query: ' + query, batch_size = self.batch_size, normalize_embeddings = True)
            text_embeddings = self.model.encode([c['chunk_text'] for c in chunks_altered], batch_size = self.batch_size, normalize_embeddings = True)
        else:
            query_embeddings = self.model.encode(query, batch_size = self.batch_size, normalize_embeddings = True)
            text_embeddings = self.model.encode([c['chunk_text'] for c in chunks], batch_size = self.batch_size, normalize_embeddings = True)
        cosine_similarities = query_embeddings @ text_embeddings.T
        chunk_similarities = text_embeddings @ text_embeddings.T

        chunks_cosine = [
            {
                **chunks[i],
                'score': float(cosine_similarities[i]),
                'index': int(i)
            }
            for i in range(len(cosine_similarities))
        ]

        cosine_only = pd.DataFrame(chunks_cosine)[['chunk_id','chunk_text', 'score', 'index']].sort_values('score', ascending = False)[:20]

        mmr_only = pd.DataFrame(self.mmr(False, chunk_similarities, chunks_cosine, k=k, fetch_k=fetch_k))
        cosine_and_mmr = pd.DataFrame(self.mmr(True, chunk_similarities, chunks_cosine, k=k, fetch_k=fetch_k))

        return [cosine_only[:k].assign(relevance_to_selected_chunks = None, mmr_score = None, model = self.model_name, score_metric = 'cosine_only', additional_tuning_descriptor = additional_tuning_descriptor), 
                mmr_only.assign(model = self.model_name, score_metric = 'mmr_only', additional_tuning_descriptor = additional_tuning_descriptor),
                cosine_and_mmr.assign(model = self.model_name, score_metric = 'cosine_and_mmr_hybrid', additional_tuning_descriptor = additional_tuning_descriptor)]



def evaluate_retriever(combos_to_tune, primary_chunk, golden_chunks):
    tuning = []
    for model in set(combos_to_tune['model']):
        for met in set(combos_to_tune['score_metric']):
            for tune_descriptor in set(combos_to_tune['additional_tuning_descriptor']):
                this_result = combos_to_tune[(combos_to_tune['model'] == model) & (combos_to_tune['score_metric'] == met) & (combos_to_tune['additional_tuning_descriptor'] == tune_descriptor)]
                if len(this_result) > 0:
                    this_result['rank'] = range(1, len(this_result)+1)
                    rank_of_primary_golden_chunk = this_result.loc[this_result['chunk_id'] == primary_chunk,'rank']
                    rank_of_golden_chunk = this_result.loc[this_result['chunk_id'].isin(golden_chunks),'rank']
                    if len(rank_of_primary_golden_chunk) > 0:
                        rank_of_primary_golden_chunk = int(min(rank_of_primary_golden_chunk))
                        contains_primary_golden_chunk = True
                        #other non-primary golden chunks:
                        contains_golden_chunk = False
                        rank_of_golden_chunk = int(min(rank_of_golden_chunk))
                    elif len(rank_of_golden_chunk) > 0:
                        rank_of_primary_golden_chunk = None
                        contains_primary_golden_chunk = False
                        rank_of_golden_chunk = int(min(rank_of_golden_chunk))
                        contains_golden_chunk = True
                    else:
                        rank_of_primary_golden_chunk = None
                        contains_primary_golden_chunk = False
                        rank_of_golden_chunk = None
                        contains_golden_chunk = False
                    tuning.append({
                        'model': model,
                        'score_metric': met,
                        'additional_tuning_descriptor': tune_descriptor,
                        'contains_primary_golden_chunk': contains_primary_golden_chunk,
                        'rank_of_primary_golden_chunk': rank_of_primary_golden_chunk,
                        'contains_acceptable_golden_chunks': contains_golden_chunk,
                        'rank_of_acceptable_golden_chunks': rank_of_golden_chunk
                    })

    return (pd.DataFrame(tuning))
                    
           
