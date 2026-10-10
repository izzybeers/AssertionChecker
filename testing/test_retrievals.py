#%%
import pandas as pd
from datetime import datetime
import numpy as np
from sentence_transformers import SentenceTransformer
from test_cases import pdf_testing_table, retrieval_tests, model_descriptions
import sys
sys.path.append("..")
from chunk_retriever import Retriever, evaluate_retriever
from helper_funs import create_chunks
from pdf_parser import parse_pdf_text



pages, blocks = parse_pdf_text(pdf_testing_table, path_prefix = '../testing/test_sources/')

support_task = "Given an author's statement, retrieve passages from the document that provide evidence supporting the statement."
contradict_task = "Given an author's statement, retrieve passages from the document that provide evidence contradicting the statement."

sources = set(r['source'] for r in retrieval_tests)
child_chunks, parent_chunks = create_chunks(pages, blocks)

k=20
fetch_k=50

t_start = datetime.now()
full_tuning_df = pd.DataFrame()
individual_retrieved_chunks = pd.DataFrame()
for source in sources:
    t_source = datetime.now()
    chunks_this_source = [c for c in child_chunks if c['source_id'] == source]
    tests_this_source = [r for r in retrieval_tests if r['source'] == source]
    print(f"{len(tests_this_source)} tests for source: {source} ({len(chunks_this_source)} chunks)")
    for row in tests_this_source:
        t_test_start = datetime.now()
        test_id = row['test_id']
        print(f"Test {test_id}")
        primary_gold_chunk_id = row['primary_gold_chunk_id']
        acceptable_gold_chunk_ids = row['gold_chunk_ids']
        statement = row['statement']

        if row['target_relation'] == 'Supports':
            task = support_task
        elif row['target_relation'] == 'Contradicts':
            task = contradict_task

        retriever = Retriever('Qwen/Qwen3-Embedding-0.6B')
        qwen_cosine_only_no_instruction, qwen_mmr_only_no_instruction, qwen_cosine_and_mmr_no_instruction = retriever.retrieve(statement, chunks_this_source, k=k, fetch_k=fetch_k, additional_tuning_descriptor = 'No instruction')
        qwen_cosine_only_with_instruction, qwen_mmr_only_with_instruction, qwen_cosine_and_mmr_with_instruction = retriever.retrieve(task + statement, chunks_this_source, k=k, fetch_k=fetch_k, additional_tuning_descriptor = 'With instruction')

        retriever = Retriever('sentence-transformers/all-MiniLM-L6-v2')
        minilm_cosine_only, minilm_mmr_only, minilm_cosine_and_mmr = retriever.retrieve(statement, chunks_this_source, k=k, fetch_k=fetch_k)

        retriever = Retriever("intfloat/e5-base-v2")
        e5_cosine_only, e5_mmr_only, e5_cosine_and_mmr = retriever.retrieve(statement, chunks_this_source, k=k, fetch_k=fetch_k)

        retriever = Retriever("BAAI/bge-base-en-v1.5")
        bge_cosine_only_no_instruction, bge_mmr_only_no_instruction, bge_cosine_and_mmr_no_instruction = retriever.retrieve(statement, chunks_this_source, k=k, fetch_k=fetch_k, additional_tuning_descriptor = 'No instruction')
        bge_cosine_only_with_instruction, bge_mmr_only_with_instruction, bge_cosine_and_mmr_with_instruction = retriever.retrieve(task + statement, chunks_this_source, k=k, fetch_k=fetch_k, additional_tuning_descriptor = 'With instruction')

        retriever = Retriever("thenlper/gte-base")
        gte_cosine_only, gte_mmr_only, gte_cosine_and_mmr = retriever.retrieve(statement, chunks_this_source, k=k, fetch_k=fetch_k)

        retriever = Retriever('jinaai/jina-embeddings-v3-hf')
        jina_cosine_only, jina_mmr_only, jina_cosine_and_mmr = retriever.retrieve(statement, chunks_this_source, k=k, fetch_k=fetch_k)

        retriever = Retriever("Hanno-Labs/dinghy-law-0.6b-v1")
        dinghy_cosine_only, dinghy_mmr_only, dinghy_cosine_and_mmr = retriever.retrieve(statement, chunks_this_source, k=k, fetch_k=fetch_k)

        print(f"Retrievals for this test took {(datetime.now() - t_test_start).total_seconds()/60} minutes")
        t_tune_start = datetime.now()
        # t1 = datetime.now()
        # print('Batch size = 2')
        # retriever = Retriever("intfloat/e5-mistral-7b-instruct", batch_size = 2)
        # print(f"Time to load model: {(datetime.now()-t1).total_seconds()/60} minutes")
        # t2 = datetime.now()
        # e5mistral_cosine_only, e5mistral_mmr_only, e5mistral_cosine_and_mmr = retriever.retrieve("Given an author's statement, retrieve passages from a legal document that support the author's assertion." + statement, chunks_this_source)
        # print(f"Time to load embeddings: {(datetime.now()-t2).total_seconds()/60} minutes")
        # t1 = datetime.now()
        # print('Batch size default')
        # retriever = Retriever("intfloat/e5-mistral-7b-instruct")
        # print(f"Time to load model: {(datetime.now()-t1).total_seconds()/60} minutes")
        # t2 = datetime.now()
        # e5mistral_cosine_only, e5mistral_mmr_only, e5mistral_cosine_and_mmr = retriever.retrieve("Given an author's statement, retrieve passages from a legal document that support the author's assertion." + statement, chunks_this_source)
        # print(f"Time to load embeddings: {(datetime.now()-t2).total_seconds()/60} minutes")

        all_tuning = pd.concat([qwen_cosine_only_no_instruction[['chunk_id','score', 'relevance_to_selected_chunks', 'mmr_score','index', 'model', 'score_metric', 'additional_tuning_descriptor']], qwen_mmr_only_no_instruction, qwen_cosine_and_mmr_no_instruction,
                                qwen_cosine_only_with_instruction[['chunk_id','score', 'relevance_to_selected_chunks', 'mmr_score','index', 'model', 'score_metric', 'additional_tuning_descriptor']], qwen_mmr_only_with_instruction, qwen_cosine_and_mmr_with_instruction,
                                minilm_cosine_only[['chunk_id','score', 'relevance_to_selected_chunks', 'mmr_score','index', 'model', 'score_metric', 'additional_tuning_descriptor']], minilm_mmr_only, minilm_cosine_and_mmr,
                                e5_cosine_only[['chunk_id','score', 'relevance_to_selected_chunks', 'mmr_score','index', 'model', 'score_metric', 'additional_tuning_descriptor']], e5_mmr_only, e5_cosine_and_mmr,
                                bge_cosine_only_no_instruction[['chunk_id','score', 'relevance_to_selected_chunks', 'mmr_score','index', 'model', 'score_metric', 'additional_tuning_descriptor']], bge_mmr_only_no_instruction, bge_cosine_and_mmr_no_instruction,
                                bge_cosine_only_with_instruction[['chunk_id','score', 'relevance_to_selected_chunks', 'mmr_score','index', 'model', 'score_metric', 'additional_tuning_descriptor']], bge_mmr_only_with_instruction, bge_cosine_and_mmr_with_instruction,
                                gte_cosine_only[['chunk_id','score', 'relevance_to_selected_chunks', 'mmr_score','index', 'model', 'score_metric', 'additional_tuning_descriptor']], gte_mmr_only, gte_cosine_and_mmr,                                              
                                jina_cosine_only[['chunk_id','score', 'relevance_to_selected_chunks', 'mmr_score','index', 'model', 'score_metric', 'additional_tuning_descriptor']], jina_mmr_only, jina_cosine_and_mmr,                                              
                                dinghy_cosine_only[['chunk_id','score', 'relevance_to_selected_chunks', 'mmr_score','index', 'model', 'score_metric', 'additional_tuning_descriptor']], dinghy_mmr_only, dinghy_cosine_and_mmr                                    
                                #e5mistral_cosine_only[['chunk_id','score', 'relevance_to_selected_chunks', 'mmr_score','index', 'model', 'score_metric', 'additional_tuning_descriptor']], e5mistral_mmr_only, e5mistral_cosine_and_mmr                                           
                                ], axis = 0)

        # all_tuning = pd.concat([e5_cosine_only[['chunk_id','score', 'relevance_to_selected_chunks', 'mmr_score','index', 'model', 'score_metric', 'additional_tuning_descriptor']], e5_mmr_only, e5_cosine_and_mmr,
        #                         bge_cosine_only_no_instruction[['chunk_id','score', 'relevance_to_selected_chunks', 'mmr_score','index', 'model', 'score_metric', 'additional_tuning_descriptor']], bge_mmr_only_no_instruction, bge_cosine_and_mmr_no_instruction,
        #                         ], axis = 0)

        individual_retrieved_chunks = pd.concat([individual_retrieved_chunks, all_tuning.assign(test = test_id)])

        print('Evaluating retrievals for this test...')
        tuning_df = evaluate_retriever(all_tuning, primary_gold_chunk_id, acceptable_gold_chunk_ids)
        full_tuning_df = pd.concat([full_tuning_df, tuning_df.assign(test_id = test_id)], axis = 0)
        print(f"Retrievals for this test took {(datetime.now() - t_tune_start).total_seconds()/60} minutes")
    print(f"Source tests took {(datetime.now() - t_source).total_seconds()/60} minutes")
print(f"Total time: {(datetime.now() - t_start).total_seconds()/60} minutes")

# full_tuning_df_extra_info = full_tuning_df.\
#     merge(model_descriptions, left_on = 'model', right_on = 'model_fullname', how = 'left')\
#         .merge(pd.DataFrame(retrieval_tests)[['test_id', 'source', 'difficulty_group', 'difficulty_score']], on = 'test_id', how='left')

full_tuning_df_10 = full_tuning_df
full_tuning_df_20 = full_tuning_df


full_tuning_df_extra_info_20 = full_tuning_df_20.\
    merge(model_descriptions, left_on = 'model', right_on = 'model_fullname', how = 'left')\
        .merge(pd.DataFrame(retrieval_tests)[['test_id', 'source', 'difficulty_group', 'difficulty_score']], on = 'test_id', how='left')


def view_summary(df, group_fields):
    return(
        df.assign(primary_hit_by_difficulty = lambda x: np.where(x['contains_primary_golden_chunk'], x['difficulty_score'], 0),
                  acceptable_hit_by_difficulty = lambda x: np.where(x['contains_primary_golden_chunk'] | x['contains_acceptable_golden_chunks'], x['difficulty_score'], 0))\
                    .groupby(group_fields, as_index=False).\
            agg(primary_hits = ('contains_primary_golden_chunk', 'sum'),
                acceptable_hits = ('contains_acceptable_golden_chunks', 'sum'),
                primary_reciprocal_hit = ('rank_of_primary_golden_chunk', lambda x: (1/x.dropna()).sum()),
                acceptable_reciprocal_hit = ('rank_of_acceptable_golden_chunks', lambda x: (1/x.dropna()).sum()),
                num_tests = ('test_id', 'size'),
                primary_hits_difficulty = ('primary_hit_by_difficulty','sum'),
                acceptable_hits_difficulty = ('acceptable_hit_by_difficulty','sum')
                )\
                    .assign(no_hits = lambda x: x['num_tests'] - x['primary_hits'] - x['acceptable_hits'],
                            weighted_hit_rate = lambda x: x['primary_hits']/x['num_tests'] + 0.5*x['acceptable_hits']/x['num_tests'],
                            weighted_hit_rate_by_difficulty = lambda x: x['primary_hits_difficulty']/x['num_tests'] + 0.5*x['acceptable_hits_difficulty']/x['num_tests'],
                            weighted_arhr = lambda x: x['primary_reciprocal_hit']/x['num_tests'] + x['acceptable_reciprocal_hit']/x['num_tests'])\
                                .sort_values(['weighted_hit_rate', 'weighted_arhr'], ascending = False)\
                                [list(group_fields) + ['num_tests', 'weighted_hit_rate', 'weighted_hit_rate_by_difficulty', 'weighted_arhr', 'primary_hits', 'acceptable_hits', 'no_hits']]
    )

view_summary(full_tuning_df_extra_info_20, ['model', 'additional_tuning_descriptor', 'score_metric'])
view_summary(full_tuning_df_extra_info_20, ['score_metric'])
view_summary(full_tuning_df_extra_info_20, ['InstructionTraining'])
view_summary(full_tuning_df_extra_info_20.query('score_metric=="cosine_only"'), ['model', 'additional_tuning_descriptor','difficulty_group']).pivot(index = ['model', 'additional_tuning_descriptor'], columns = 'difficulty_group', values = 'weighted_hit_rate')


#%%