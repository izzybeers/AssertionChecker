import pandas as pd

format_pages = lambda pages: ",".join(
    "None" if p is None else str(p)
    for p in pages
)

pdf_testing_table = [
    {
        "file_name": "Kropf_DOJ_Outsourcing_Under_Fire_Again_2023.pdf",
        "pincite_type": None,
        "reporter_start_page": None,
        "expected_page_display_numbers": format_pages(range(1, 9))
    },
    {
        "file_name": "EU_Directive_2017_828_Long_Term_Shareholder_Engagement.pdf",
        "pincite_type": None,
        "reporter_start_page": None,
        "expected_page_display_numbers": format_pages(range(1, 36))
    },
    {
        "file_name": "National_Cycle_v_Savoy_Reinsurance_1991.pdf",
        "pincite_type": "standard",
        "reporter_start_page": 61,
        "expected_page_display_numbers": format_pages(range(61, 66))
    },
    {
        "file_name": "AgangaWilliams_Nabutovsky_Outsourcing_Ruling_5_Years_On_2024.pdf",
        "pincite_type": None,
        "reporter_start_page": None,
        "expected_page_display_numbers": format_pages(range(1, 9))
    },
    {
        "file_name": "Unocal_v_Mesa_Petroleum_1985.pdf",
        "pincite_type": "standard",
        "reporter_start_page": 946,
        "expected_page_display_numbers": format_pages(range(1, 15))
    },
    {
        "file_name": "Cleary_Gottlieb_SDNY_Outsourcing_Investigation_Fifth_Amendment_2019.pdf",
        "pincite_type": None,
        "reporter_start_page": None,
        "expected_page_display_numbers": format_pages([None, 2, 3, 4, 5, 6])
    },
    {
        "file_name": "United_States_v_Connolly_2019.pdf",
        "pincite_type": "star",
        "reporter_start_page": None,
        "expected_page_display_numbers": format_pages(range(1, 23))
    },
    {
        "file_name": "Massey_et_al_US_v_Connolly_Outsourcing_and_How_to_Avoid_It_2019.pdf",
        "pincite_type": None,
        "reporter_start_page": None,
        "expected_page_display_numbers": format_pages(range(1, 7))
    },
    {
        "file_name": "Sarkki_et_al_Balancing_Credibility_Relevance_and_Legitimacy_2013.pdf",
        "pincite_type": None,
        "reporter_start_page": None,
        "expected_page_display_numbers": format_pages(range(1, 36))
    },
    {
        "file_name": "Lajoux_Latest_Delaware_Decisions_and_the_Business_Judgment_Rule_2024.pdf",
        "pincite_type": None,
        "reporter_start_page": None,
        "expected_page_display_numbers": format_pages([None])
    },
    {
        "file_name": "Revlon_v_MacAndrews_Forbes_1986.pdf",
        "pincite_type": "standard",
        "reporter_start_page": 173,
        "expected_page_display_numbers": format_pages(range(1, 14))
    },
    {
        "file_name": "Cheffins_Delaware_and_the_Transformation_of_Corporate_Governance_2015.pdf",
        "pincite_type": None,
        "reporter_start_page": None,
        "expected_page_display_numbers": format_pages(
            ([None] * 5) + list(range(1, 94)) + ([None] * 3)
        )
    },
    {
        "file_name": "Reuters_Exonerated_Trader_Resolves_Deutsche_Bank_Lawsuit_2024.pdf",
        "pincite_type": None,
        "reporter_start_page": None,
        "expected_page_display_numbers": format_pages(range(1, 13))
    },
    {
        "file_name": "Prince_Predictability_of_the_Court_System.pdf",
        "pincite_type": None,
        "reporter_start_page": None,
        "expected_page_display_numbers": format_pages([None])
    },
    {
        "file_name": "United_States_v_Armbruster_2021.pdf",
        "pincite_type": "star",
        "reporter_start_page": None,
        "expected_page_display_numbers": format_pages(range(1, 5))
    },
    {
        "file_name": "Reuters_Lloyds_Settles_ExTrader_Unfair_Dismissal_2015.pdf",
        "pincite_type": None,
        "reporter_start_page": None,
        "expected_page_display_numbers": format_pages(range(1, 11))
    }
]

reading_order_tests = [
    {
        "source_id": "National_Cycle_v_Savoy_Reinsurance_1991",
        "page_index": 0,
        "phrases_in_order": [
            "therefore be regarded",
            "Court is hereby AF-",
            "Insured filed diversity action against"
        ]
    },
    {
        "source_id": "National_Cycle_v_Savoy_Reinsurance_1991",
        "page_index": 2,
        "phrases_in_order": [
            "In June it sent National Cycle a new endorse-",
            "Neither before nor since has it lifted a finger",
            "The district court ordered Savoy"
        ]
    },
    {
        "source_id": "National_Cycle_v_Savoy_Reinsurance_1991",
        "page_index": 3,
        "phrases_in_order": [
            "Ibid.",
            "[2] This is not tidy",
            "[3] Green"
        ]
    }
]

pincite_tests = [
    # Ordinary PDF: pincite == displayed PDF page
    {
        "source_id": "Kropf_DOJ_Outsourcing_Under_Fire_Again_2023",
        "expected_pincite": 2,
        "text": "The Connolly standard is high."
    },
    {
        "source_id": "Massey_et_al_US_v_Connolly_Outsourcing_and_How_to_Avoid_It_2019",
        "expected_pincite": 1,
        "text": "On May 2, in a widely-watched case"
    },
    # Standard reporter pagination: National Cycle
    {
        "source_id": "National_Cycle_v_Savoy_Reinsurance_1991",
        "expected_pincite": 61,
        "text": "Insured filed diversity action against"
    },
    {
        "source_id": "National_Cycle_v_Savoy_Reinsurance_1991",
        "expected_pincite": 63,
        "text": "Neither before nor since has it lifted a finger"
    },
    {
        "source_id": "National_Cycle_v_Savoy_Reinsurance_1991",
        "expected_pincite": 64,
        "text": "[2] This is not tidy"
    },
    # Star pincites: Connolly
    {
        "source_id": "United_States_v_Connolly_2019",
        "expected_pincite": 1,
        "text": "*1 Black moves for relief under United States v. Kastigar"
    },
    # Tests carryover BEFORE the *2 marker
    {
        "source_id": "United_States_v_Connolly_2019",
        "expected_pincite": 1,
        "text": "The following facts reflect what the Court knows about"
    },
    {
        "source_id": "United_States_v_Connolly_2019",
        "expected_pincite": 2,
        "text": "*2 In 2010, the Government started looking at another"
    },
    # Much later star pincite -- useful to make sure propagation
    # still works well beyond *1/*2
    {
        "source_id": "United_States_v_Connolly_2019",
        "expected_pincite": 10,
        "text": "*10 In short, while the record before the Court is incomplete"
    },
    {
        "source_id": "Kropf_DOJ_Outsourcing_Under_Fire_Again_2023",
        "expected_pincite": "2",
        "text": "The Connolly standard is high."
    },
    # Star pincites: Armbruster
    {
        "source_id": "United_States_v_Armbruster_2021",
        "expected_pincite": 1,
        "text": "*1 The government charged the defendants"
    },
    {
        "source_id": "United_States_v_Armbruster_2021",
        "expected_pincite": 2,
        "text": "*2 Wogsland has filed substantive objections"
    },
    {
        "source_id": "United_States_v_Armbruster_2021",
        "expected_pincite": 3,
        "text": "*3 As the magistrate judge noted"
    },
    {
        "source_id": "United_States_v_Armbruster_2021",
        "expected_pincite": 4,
        "text": "*4 THEREFORE, IT IS ORDERED"
    },
    # Standard reporter pagination: Unocal
    # These are especially useful because they test an actual
    # reporter-page transition within the Westlaw PDF.
    {
        "source_id": "Unocal_v_Mesa_Petroleum_1985",
        "expected_pincite": 954,
        "text": "Delaware corporation may deal selectively with its"
    },
    {
        "source_id": "Unocal_v_Mesa_Petroleum_1985",
        "expected_pincite": 955,
        "text": "We must bear in mind the inherent danger in the"
    },
    # Standard reporter pagination: Revlon
    {
        "source_id": "Revlon_v_MacAndrews_Forbes_1986",
        "expected_pincite": 181,
        "text": "debts incurred, and retain the profit for itself"
    },
    {
        "source_id": "Revlon_v_MacAndrews_Forbes_1986",
        "expected_pincite": 182,
        "text": "However, when Pantry Pride increased its offer to $50"
    },
    {
        "source_id": "Revlon_v_MacAndrews_Forbes_1986",
        "expected_pincite": 184,
        "text": "protection, and (3) higher price"
    },
]

retrieval_tests = [

    # =========================================================
    # REVLON
    # =========================================================

    {
        "test_id": "R01",
        "source": "Revlon_v_MacAndrews_Forbes_1986",
        "statement": (
            "The Notes issued in Revlon's exchange offer restricted the "
            "company's ability to incur additional debt, sell assets, or "
            "pay dividends unless independent directors approved."
        ),
        "primary_gold_chunk_id":
            "Revlon_v_MacAndrews_Forbes_1986page5paragraph7",
        "gold_chunk_ids": {
            "Revlon_v_MacAndrews_Forbes_1986page5paragraph6",
            "Revlon_v_MacAndrews_Forbes_1986page5paragraph7",
        },
        "gold_pincite": "177",
        "gold_parent_chunk_id":
            "Revlon_v_MacAndrews_Forbes_1986page5",
        "target_relation": "Supports",
        "difficulty": "factual_paraphrase",
        "difficulty_group": "factual",
        "difficulty_score": 2,
    },

    {
        "test_id": "R02",
        "source": "Revlon_v_MacAndrews_Forbes_1986",
        "statement": (
            "Under the October 3 Forstmann proposal, Revlon shareholders "
            "would receive $56 per share, Forstmann would assume Revlon's "
            "Note debt, and Revlon would waive the Rights and Note covenants "
            "for Forstmann or a superior offer."
        ),
        "primary_gold_chunk_id":
            "Revlon_v_MacAndrews_Forbes_1986page5paragraph17",
        "gold_chunk_ids": {
            "Revlon_v_MacAndrews_Forbes_1986page5paragraph16",
            "Revlon_v_MacAndrews_Forbes_1986page5paragraph17",
        },
        "gold_pincite": "178",
        "gold_parent_chunk_id":
            "Revlon_v_MacAndrews_Forbes_1986page5",
        "target_relation": "Supports",
        "difficulty": "compound_factual",
        "difficulty_group": "factual",
        "difficulty_score": 2,
    },

    {
        "test_id": "R03",
        "source": "Revlon_v_MacAndrews_Forbes_1986",
        "statement": (
            "Revlon held that lock-ups and related agreements are "
            "categorically unlawful under Delaware law."
        ),
        "primary_gold_chunk_id":
            "Revlon_v_MacAndrews_Forbes_1986page4paragraph16",
        "gold_chunk_ids": {
            "Revlon_v_MacAndrews_Forbes_1986page4paragraph16",
            "Revlon_v_MacAndrews_Forbes_1986page4paragraph17",
            "Revlon_v_MacAndrews_Forbes_1986page4paragraph18",
        },
        "gold_pincite": "177",
        "gold_parent_chunk_id":
            "Revlon_v_MacAndrews_Forbes_1986page4",
        "target_relation": "Contradicts",
        "difficulty": "negation_hard_negative",
        "difficulty_group": "contradiction",
        "difficulty_score": 3,
    },

    {
        "test_id": "R04",
        "source": "Revlon_v_MacAndrews_Forbes_1986",
        "statement": (
            "By October 12, Revlon had resolved to redeem the Rights in "
            "connection with any cash proposal of at least $57.25 per share, "
            "and the Rights were no longer an impediment to the takeover contest."
        ),
        "primary_gold_chunk_id":
            "Revlon_v_MacAndrews_Forbes_1986page7paragraph23",
        "gold_chunk_ids": {
            "Revlon_v_MacAndrews_Forbes_1986page7paragraph23",
        },
        "gold_pincite": "181",
        "gold_parent_chunk_id":
            "Revlon_v_MacAndrews_Forbes_1986page7",
        "target_relation": "Supports",
        "difficulty": "factual_paraphrase",
        "difficulty_group": "factual",
        "difficulty_score": 2,
    },

    {
        "test_id": "R05",
        "source": "Revlon_v_MacAndrews_Forbes_1986",
        "statement": (
            "Revlon's Rights Plan generally became effective when someone "
            "acquired beneficial ownership of twenty percent or more of the "
            "company's shares."
        ),
        "primary_gold_chunk_id":
            "Revlon_v_MacAndrews_Forbes_1986page5paragraph3",
        "gold_chunk_ids": {
            "Revlon_v_MacAndrews_Forbes_1986page5paragraph3",
            "Revlon_v_MacAndrews_Forbes_1986page5paragraph4",
            "Revlon_v_MacAndrews_Forbes_1986page5paragraph5",
        },
        "gold_pincite": "177",
        "gold_parent_chunk_id":
            "Revlon_v_MacAndrews_Forbes_1986page5",
        "target_relation": "Supports",
        "difficulty": "easy_lexical",
        "difficulty_group": "factual",
        "difficulty_score": 1,
    },

    {
        "test_id": "R06",
        "source": "Revlon_v_MacAndrews_Forbes_1986",
        "statement": (
            "After the Forstmann merger and waiver of the Note covenants "
            "were announced, the Notes fell from around par value to 87.50."
        ),
        "primary_gold_chunk_id":
            "Revlon_v_MacAndrews_Forbes_1986page5paragraph17",
        "gold_chunk_ids": {
            "Revlon_v_MacAndrews_Forbes_1986page5paragraph16",
            "Revlon_v_MacAndrews_Forbes_1986page5paragraph17",
        },
        "gold_pincite": "178",
        "gold_parent_chunk_id":
            "Revlon_v_MacAndrews_Forbes_1986page5",
        "target_relation": "Supports",
        "difficulty": "numeric_factual",
        "difficulty_group": "factual",
        "difficulty_score": 1,
    },

    # NEW — factual
    {
        "test_id": "R07",
        "source": "Revlon_v_MacAndrews_Forbes_1986",
        "statement": (
            "Pantry Pride's first hostile tender offer proposed $47.50 per "
            "common share and $26.67 per preferred share and was conditioned "
            "on obtaining financing and eliminating the Rights."
        ),
        "primary_gold_chunk_id":
            "Revlon_v_MacAndrews_Forbes_1986page5paragraph6",
        "gold_chunk_ids": {
            "Revlon_v_MacAndrews_Forbes_1986page5paragraph4",
            "Revlon_v_MacAndrews_Forbes_1986page5paragraph5",
            "Revlon_v_MacAndrews_Forbes_1986page5paragraph6",
        },
        "gold_pincite": "177",
        "gold_parent_chunk_id":
            "Revlon_v_MacAndrews_Forbes_1986page5",
        "target_relation": "Supports",
        "difficulty": "compound_numeric_factual",
        "difficulty_group": "factual",
        "difficulty_score": 2,
    },

    # NEW — factual
    {
        "test_id": "R08",
        "source": "Revlon_v_MacAndrews_Forbes_1986",
        "statement": (
            "Under Revlon's Rights Plan, each common share carried a right "
            "exchangeable for a $65 principal note paying twelve percent "
            "interest and maturing in one year."
        ),
        "primary_gold_chunk_id":
            "Revlon_v_MacAndrews_Forbes_1986page5paragraph3",
        "gold_chunk_ids": {
            "Revlon_v_MacAndrews_Forbes_1986page5paragraph3",
            "Revlon_v_MacAndrews_Forbes_1986page5paragraph4",
            "Revlon_v_MacAndrews_Forbes_1986page5paragraph5",
        },
        "gold_pincite": "177",
        "gold_parent_chunk_id":
            "Revlon_v_MacAndrews_Forbes_1986page5",
        "target_relation": "Supports",
        "difficulty": "numeric_factual",
        "difficulty_group": "factual",
        "difficulty_score": 1,
    },

    # NEW — legal rule
    {
        "test_id": "R09",
        "source": "Revlon_v_MacAndrews_Forbes_1986",
        "statement": (
            "When responding to a takeover threat, directors may consider "
            "non-stockholder constituencies only when doing so provides some "
            "rationally related benefit to stockholders."
        ),
        "primary_gold_chunk_id":
            "Revlon_v_MacAndrews_Forbes_1986page4paragraph16",
        "gold_chunk_ids": {
            "Revlon_v_MacAndrews_Forbes_1986page4paragraph16",
            "Revlon_v_MacAndrews_Forbes_1986page4paragraph17",
            "Revlon_v_MacAndrews_Forbes_1986page4paragraph18",
        },
        "gold_pincite": "177",
        "gold_parent_chunk_id":
            "Revlon_v_MacAndrews_Forbes_1986page4",
        "target_relation": "Supports",
        "difficulty": "legal_rule_paraphrase",
        "difficulty_group": "legal_rule",
        "difficulty_score": 2,
    },

    # NEW — contradiction
    {
        "test_id": "R10",
        "source": "Revlon_v_MacAndrews_Forbes_1986",
        "statement": (
            "Even after the sale of Revlon became inevitable, the board's "
            "primary duty remained preserving Revlon as an independent "
            "corporate entity rather than maximizing its sale value."
        ),
        "primary_gold_chunk_id":
            "Revlon_v_MacAndrews_Forbes_1986page8paragraph9",
        "gold_chunk_ids": {
            "Revlon_v_MacAndrews_Forbes_1986page8paragraph9",
            "Revlon_v_MacAndrews_Forbes_1986page8paragraph10",
        },
        "gold_pincite": "182",
        "gold_parent_chunk_id":
            "Revlon_v_MacAndrews_Forbes_1986page8",
        "target_relation": "Contradicts",
        "difficulty": "negation_legal_reasoning",
        "difficulty_group": "contradiction",
        "difficulty_score": 3,
    },


    # =========================================================
    # CONNOLLY
    # =========================================================

    {
        "test_id": "C01",
        "source": "United_States_v_Connolly_2019",
        "statement": (
            "A Fifth Amendment self-incrimination claim requires both "
            "coercion and conduct attributable to the government."
        ),
        "primary_gold_chunk_id":
            "United_States_v_Connolly_2019page8paragraph4",
        "gold_chunk_ids": {
            "United_States_v_Connolly_2019page8paragraph4",
            "United_States_v_Connolly_2019page8paragraph5",
            "United_States_v_Connolly_2019page8paragraph6",
        },
        "gold_pincite": "10",
        "gold_parent_chunk_id":
            "United_States_v_Connolly_2019page8",
        "target_relation": "Supports",
        "difficulty": "legal_rule",
        "difficulty_group": "legal_rule",
        "difficulty_score": 2,
    },

    {
        "test_id": "C02",
        "source": "United_States_v_Connolly_2019",
        "statement": (
            "Deutsche Bank's first interview of Gavin Black was conducted "
            "at the government's behest, years before the government itself "
            "made an effort to speak with him."
        ),
        "primary_gold_chunk_id":
            "United_States_v_Connolly_2019page9paragraph4",
        "gold_chunk_ids": {
            "United_States_v_Connolly_2019page9paragraph4",
        },
        "gold_pincite": "11",
        "gold_parent_chunk_id":
            "United_States_v_Connolly_2019page9",
        "target_relation": "Supports",
        "difficulty": "factual_paraphrase",
        "difficulty_group": "factual",
        "difficulty_score": 2,
    },

    {
        "test_id": "C03",
        "source": "United_States_v_Connolly_2019",
        "statement": (
            "The government's four LIBOR interviews conducted before "
            "Black's first Paul Weiss interview involved employees of "
            "another panel bank and provided little evidence of a genuine "
            "parallel Deutsche Bank investigation."
        ),
        "primary_gold_chunk_id":
            "United_States_v_Connolly_2019page10paragraph6",
        "gold_chunk_ids": {
            "United_States_v_Connolly_2019page10paragraph6",
        },
        "gold_pincite": "12",
        "gold_parent_chunk_id":
            "United_States_v_Connolly_2019page10",
        "target_relation": "Supports",
        "difficulty": "reasoning_paraphrase",
        "difficulty_group": "reasoning",
        "difficulty_score": 3,
    },

    {
        "test_id": "C04",
        "source": "United_States_v_Connolly_2019",
        "statement": (
            "The court reasoned that Paul Weiss performed work the "
            "government itself could, should, and would have performed, "
            "while the record contained little evidence of independent "
            "government investigative work."
        ),
        "primary_gold_chunk_id":
            "United_States_v_Connolly_2019page10paragraph3",
        "gold_chunk_ids": {
            "United_States_v_Connolly_2019page10paragraph3",
        },
        "gold_pincite": "12",
        "gold_parent_chunk_id":
            "United_States_v_Connolly_2019page10",
        "target_relation": "Supports",
        "difficulty": "reasoning_paraphrase",
        "difficulty_group": "reasoning",
        "difficulty_score": 3,
    },

    {
        "test_id": "C05",
        "source": "United_States_v_Connolly_2019",
        "statement": (
            "Even assuming Deutsche Bank and Paul Weiss were government "
            "agents for Garrity purposes, the court concluded that Black's "
            "Kastigar rights had not been violated."
        ),
        "primary_gold_chunk_id":
            "United_States_v_Connolly_2019page0paragraph22",
        "gold_chunk_ids": {
            "United_States_v_Connolly_2019page0paragraph21",
            "United_States_v_Connolly_2019page0paragraph22",
        },
        "gold_pincite": "1",
        "gold_parent_chunk_id":
            "United_States_v_Connolly_2019page0",
        "target_relation": "Supports",
        "difficulty": "conditional_legal_reasoning",
        "difficulty_group": "reasoning",
        "difficulty_score": 3,
    },

    {
        "test_id": "C06",
        "source": "United_States_v_Connolly_2019",
        "statement": (
            "The court treated protection of the defendant's constitutional "
            "right against self-incrimination as more important than the "
            "government's interest in the convenience of outsourcing investigative work."
        ),
        "primary_gold_chunk_id":
            "United_States_v_Connolly_2019page11paragraph8",
        "gold_chunk_ids": {
            "United_States_v_Connolly_2019page11paragraph8",
        },
        "gold_pincite": "14",
        "gold_parent_chunk_id":
            "United_States_v_Connolly_2019page11",
        "target_relation": "Supports",
        "difficulty": "abstract_paraphrase",
        "difficulty_group": "reasoning",
        "difficulty_score": 3,
    },

    # NEW — reasoning
    {
        "test_id": "C07",
        "source": "United_States_v_Connolly_2019",
        "statement": (
            "The court drew an unfavorable inference from the government's "
            "incomplete record and concluded that the United States appeared "
            "to have outsourced its investigation to Deutsche Bank and its lawyers."
        ),
        "primary_gold_chunk_id":
            "United_States_v_Connolly_2019page7paragraph11",
        "gold_chunk_ids": {
            "United_States_v_Connolly_2019page7paragraph11",
            "United_States_v_Connolly_2019page7paragraph12",
        },
        "gold_pincite": "10",
        "gold_parent_chunk_id":
            "United_States_v_Connolly_2019page7",
        "target_relation": "Supports",
        "difficulty": "reasoning_paraphrase",
        "difficulty_group": "reasoning",
        "difficulty_score": 3,
    },

    # NEW — reasoning
    {
        "test_id": "C08",
        "source": "United_States_v_Connolly_2019",
        "statement": (
            "Rather than independently developing its investigation of Gavin "
            "Black, the government built on a foundation created by Deutsche "
            "Bank and its lawyers, who had effectively interviewed employees "
            "and provided the resulting questions and answers to investigators."
        ),
        "primary_gold_chunk_id":
            "United_States_v_Connolly_2019page9paragraph9",
        "gold_chunk_ids": {
            "United_States_v_Connolly_2019page9paragraph9",
        },
        "gold_pincite": "12",
        "gold_parent_chunk_id":
            "United_States_v_Connolly_2019page9",
        "target_relation": "Supports",
        "difficulty": "reasoning_paraphrase",
        "difficulty_group": "reasoning",
        "difficulty_score": 3,
    },


    # =========================================================
    # UNOCAL
    # =========================================================

    {
        "test_id": "U01",
        "source": "Unocal_v_Mesa_Petroleum_1985",
        "statement": (
            "The board's power to respond to threats derives from its "
            "duty to protect the corporate enterprise, including stockholders, "
            "from reasonably perceived harm regardless of the source."
        ),
        "primary_gold_chunk_id":
            "Unocal_v_Mesa_Petroleum_1985page7paragraph24",
        "gold_chunk_ids": {
            "Unocal_v_Mesa_Petroleum_1985page7paragraph24",
            "Unocal_v_Mesa_Petroleum_1985page7paragraph25",
        },
        "gold_pincite": "954",
        "gold_parent_chunk_id":
            "Unocal_v_Mesa_Petroleum_1985page7",
        "target_relation": "Supports",
        "difficulty": "legal_rule_paraphrase",
        "difficulty_group": "legal_rule",
        "difficulty_score": 2,
    },

    {
        "test_id": "U02",
        "source": "Unocal_v_Mesa_Petroleum_1985",
        "statement": (
            "When a board confronts a pending takeover bid, it must determine "
            "whether the offer is in the best interests of the corporation "
            "and its shareholders."
        ),
        "primary_gold_chunk_id":
            "Unocal_v_Mesa_Petroleum_1985page8paragraph16",
        "gold_chunk_ids": {
            "Unocal_v_Mesa_Petroleum_1985page8paragraph16",
            "Unocal_v_Mesa_Petroleum_1985page8paragraph17",
            "Unocal_v_Mesa_Petroleum_1985page8paragraph18",
        },
        "gold_pincite": "954",
        "gold_parent_chunk_id":
            "Unocal_v_Mesa_Petroleum_1985page8",
        "target_relation": "Supports",
        "difficulty": "legal_rule",
        "difficulty_group": "legal_rule",
        "difficulty_score": 2,
    },

    {
        "test_id": "U03",
        "source": "Unocal_v_Mesa_Petroleum_1985",
        "statement": (
            "Unocal gave a corporation unbridled discretion to defeat any "
            "perceived takeover threat by whatever Draconian means were available."
        ),
        "primary_gold_chunk_id":
            "Unocal_v_Mesa_Petroleum_1985page8paragraph26",
        "gold_chunk_ids": {
            "Unocal_v_Mesa_Petroleum_1985page8paragraph26",
            "Unocal_v_Mesa_Petroleum_1985page8paragraph27",
            "Unocal_v_Mesa_Petroleum_1985page8paragraph28",
        },
        "gold_pincite": "955",
        "gold_parent_chunk_id":
            "Unocal_v_Mesa_Petroleum_1985page8",
        "target_relation": "Contradicts",
        "difficulty": "negation_hard_negative",
        "difficulty_group": "contradiction",
        "difficulty_score": 3,
    },

    {
        "test_id": "U04",
        "source": "Unocal_v_Mesa_Petroleum_1985",
        "statement": (
            "In evaluating a takeover threat, directors may consider the "
            "adequacy of the price, the nature and timing of the offer, "
            "legality concerns, effects on non-shareholder constituencies, "
            "the risk of nonconsummation, and the quality of the securities offered."
        ),
        "primary_gold_chunk_id":
            "Unocal_v_Mesa_Petroleum_1985page9paragraph6",
        "gold_chunk_ids": {
            "Unocal_v_Mesa_Petroleum_1985page9paragraph6",
            "Unocal_v_Mesa_Petroleum_1985page9paragraph7",
        },
        "gold_pincite": "955",
        "gold_parent_chunk_id":
            "Unocal_v_Mesa_Petroleum_1985page9",
        "target_relation": "Supports",
        "difficulty": "compound_legal_rule",
        "difficulty_group": "legal_rule",
        "difficulty_score": 3,
    },

    {
        "test_id": "U05",
        "source": "Unocal_v_Mesa_Petroleum_1985",
        "statement": (
            "In matters involving fundamental corporate change, "
            "Unocal rejected the conception of the board as merely a "
            "passive instrumentality."
        ),
        "primary_gold_chunk_id":
            "Unocal_v_Mesa_Petroleum_1985page8paragraph2",
        "gold_chunk_ids": {
            "Unocal_v_Mesa_Petroleum_1985page8paragraph2",
        },
        "gold_pincite": "954",
        "gold_parent_chunk_id":
            "Unocal_v_Mesa_Petroleum_1985page8",
        "target_relation": "Supports",
        "difficulty": "abstract_paraphrase",
        "difficulty_group": "reasoning",
        "difficulty_score": 3,
    },

    # NEW — legal rule
    {
        "test_id": "U06",
        "source": "Unocal_v_Mesa_Petroleum_1985",
        "statement": (
            "A Delaware corporation may deal selectively with its "
            "stockholders so long as the directors are not acting for the "
            "sole or primary purpose of entrenching themselves in office."
        ),
        "primary_gold_chunk_id":
            "Unocal_v_Mesa_Petroleum_1985page7paragraph22",
        "gold_chunk_ids": {
            "Unocal_v_Mesa_Petroleum_1985page7paragraph22",
            "Unocal_v_Mesa_Petroleum_1985page7paragraph23",
        },
        "gold_pincite": "954",
        "gold_parent_chunk_id":
            "Unocal_v_Mesa_Petroleum_1985page7",
        "target_relation": "Supports",
        "difficulty": "legal_rule_paraphrase",
        "difficulty_group": "legal_rule",
        "difficulty_score": 2,
    },

    # NEW — legal rule
    {
        "test_id": "U07",
        "source": "Unocal_v_Mesa_Petroleum_1985",
        "statement": (
            "Because directors responding to a takeover bid may act primarily "
            "in their own interests, their actions receive threshold judicial "
            "scrutiny before they obtain the protection of the business judgment rule."
        ),
        "primary_gold_chunk_id":
            "Unocal_v_Mesa_Petroleum_1985page8paragraph16",
        "gold_chunk_ids": {
            "Unocal_v_Mesa_Petroleum_1985page8paragraph16",
            "Unocal_v_Mesa_Petroleum_1985page8paragraph17",
            "Unocal_v_Mesa_Petroleum_1985page8paragraph18",
        },
        "gold_pincite": "954",
        "gold_parent_chunk_id":
            "Unocal_v_Mesa_Petroleum_1985page8",
        "target_relation": "Supports",
        "difficulty": "legal_rule_paraphrase",
        "difficulty_group": "legal_rule",
        "difficulty_score": 2,
    },

    # NEW — legal rule
    {
        "test_id": "U08",
        "source": "Unocal_v_Mesa_Petroleum_1985",
        "statement": (
            "For a defensive measure to receive business-judgment-rule "
            "protection, it must be reasonable in relation to the threat posed."
        ),
        "primary_gold_chunk_id":
            "Unocal_v_Mesa_Petroleum_1985page9paragraph6",
        "gold_chunk_ids": {
            "Unocal_v_Mesa_Petroleum_1985page9paragraph6",
            "Unocal_v_Mesa_Petroleum_1985page9paragraph7",
        },
        "gold_pincite": "955",
        "gold_parent_chunk_id":
            "Unocal_v_Mesa_Petroleum_1985page9",
        "target_relation": "Supports",
        "difficulty": "legal_rule",
        "difficulty_group": "legal_rule",
        "difficulty_score": 2,
    },

    # NEW — contradiction
    {
        "test_id": "U09",
        "source": "Unocal_v_Mesa_Petroleum_1985",
        "statement": (
            "Unocal permits directors to use a selective stock repurchase "
            "solely or primarily to perpetuate themselves in office."
        ),
        "primary_gold_chunk_id":
            "Unocal_v_Mesa_Petroleum_1985page8paragraph30",
        "gold_chunk_ids": {
            "Unocal_v_Mesa_Petroleum_1985page8paragraph30",
            "Unocal_v_Mesa_Petroleum_1985page8paragraph31",
            "Unocal_v_Mesa_Petroleum_1985page8paragraph32",
        },
        "gold_pincite": "955",
        "gold_parent_chunk_id":
            "Unocal_v_Mesa_Petroleum_1985page8",
        "target_relation": "Contradicts",
        "difficulty": "negation_legal_rule",
        "difficulty_group": "contradiction",
        "difficulty_score": 3,
    },

    # NEW — contradiction
    {
        "test_id": "U10",
        "source": "Unocal_v_Mesa_Petroleum_1985",
        "statement": (
            "Under Unocal, whether a defensive measure is reasonable in "
            "relation to the takeover threat is irrelevant to whether the "
            "measure receives business-judgment-rule protection."
        ),
        "primary_gold_chunk_id":
            "Unocal_v_Mesa_Petroleum_1985page9paragraph6",
        "gold_chunk_ids": {
            "Unocal_v_Mesa_Petroleum_1985page9paragraph6",
            "Unocal_v_Mesa_Petroleum_1985page9paragraph7",
        },
        "gold_pincite": "955",
        "gold_parent_chunk_id":
            "Unocal_v_Mesa_Petroleum_1985page9",
        "target_relation": "Contradicts",
        "difficulty": "negation_legal_rule",
        "difficulty_group": "contradiction",
        "difficulty_score": 3,
    },

    # NEW — contradiction
    {
        "test_id": "U11",
        "source": "Unocal_v_Mesa_Petroleum_1985",
        "statement": (
            "Approval by a majority of outside independent directors does "
            "not strengthen a board's proof that its response to a takeover "
            "threat was proper."
        ),
        "primary_gold_chunk_id":
            "Unocal_v_Mesa_Petroleum_1985page8paragraph5",
        "gold_chunk_ids": {
            "Unocal_v_Mesa_Petroleum_1985page8paragraph5",
            "Unocal_v_Mesa_Petroleum_1985page8paragraph6",
            "Unocal_v_Mesa_Petroleum_1985page8paragraph7",
        },
        "gold_pincite": "954",
        "gold_parent_chunk_id":
            "Unocal_v_Mesa_Petroleum_1985page8",
        "target_relation": "Contradicts",
        "difficulty": "negation_legal_rule",
        "difficulty_group": "contradiction",
        "difficulty_score": 3,
    },


    # =========================================================
    # KROPF
    # =========================================================

    {
        "test_id": "K01",
        "source": "Kropf_DOJ_Outsourcing_Under_Fire_Again_2023",
        "statement": (
            "Kropf described the difficult Garrity question as whether an "
            "interview conducted by a cooperating private company remains "
            "the company's interview or effectively becomes the government's interview."
        ),
        "primary_gold_chunk_id":
            "Kropf_DOJ_Outsourcing_Under_Fire_Again_2023page1paragraph5",
        "gold_chunk_ids": {
            "Kropf_DOJ_Outsourcing_Under_Fire_Again_2023page1paragraph5",
        },
        "gold_pincite": "2",
        "gold_parent_chunk_id":
            "Kropf_DOJ_Outsourcing_Under_Fire_Again_2023page1",
        "target_relation": "Supports",
        "difficulty": "conceptual_paraphrase",
        "difficulty_group": "reasoning",
        "difficulty_score": 2,
    },

    {
        "test_id": "K02",
        "source": "Kropf_DOJ_Outsourcing_Under_Fire_Again_2023",
        "statement": (
            "Kropf's description of Connolly required only government "
            "direction of the employer's interview; coercion of the employee "
            "was unnecessary."
        ),
        "primary_gold_chunk_id":
            "Kropf_DOJ_Outsourcing_Under_Fire_Again_2023page1paragraph7",
        "gold_chunk_ids": {
            "Kropf_DOJ_Outsourcing_Under_Fire_Again_2023page1paragraph7",
        },
        "gold_pincite": "2",
        "gold_parent_chunk_id":
            "Kropf_DOJ_Outsourcing_Under_Fire_Again_2023page1",
        "target_relation": "Contradicts",
        "difficulty": "negation_hard_negative",
        "difficulty_group": "contradiction",
        "difficulty_score": 3,
    },


    # =========================================================
    # ARMBRUSTER
    # =========================================================

    {
        "test_id": "A01",
        "source": "United_States_v_Armbruster_2021",
        "statement": (
            "Under the federal immunity statute, the burden shifts to the "
            "government without the defendant first showing that he testified "
            "under a grant of immunity."
        ),
        "primary_gold_chunk_id":
            "United_States_v_Armbruster_2021page3paragraph7",
        "gold_chunk_ids": {
            "United_States_v_Armbruster_2021page3paragraph7",
        },
        "gold_pincite": "4",
        "gold_parent_chunk_id":
            "United_States_v_Armbruster_2021page3",
        "target_relation": "Contradicts",
        "difficulty": "negation_legal_rule",
        "difficulty_group": "contradiction",
        "difficulty_score": 3,
    }

]
assertion_test_cases = [
    # =========================================================
    # CONNOLLY
    # =========================================================
    {
        'source': 'United_States_v_Connolly_2019',
        'pincite': '10',
        'statement': 'The court stated that the United States appeared to have outsourced its investigation to Deutsche Bank and its lawyers.',
        'expected_conclusion': 'Supports At Cited Location'
    },
    {
        'source': 'United_States_v_Connolly_2019',
        'pincite': '10',
        'statement': '"everything I have read suggests that the United States outsourced its investigation to Deutsche Bank and its lawyers."',
        'expected_conclusion': 'Exact Quote Match'
    },
    {
        'source': 'United_States_v_Connolly_2019',
        'pincite': '9',
        'statement': '"everything I have read suggests that the United States outsourced its investigation to Deutsche Bank and its lawyers."',
        'expected_conclusion': 'Exact Quote Match In Other Location'
    },
    {
        'source': 'United_States_v_Connolly_2019',
        'pincite': '9-10',
        'statement': '"everything I have read suggests that the United States outsourced its investigation to Deutsche Bank and its lawyers."',
        'expected_conclusion': 'Exact Quote Match'
    },
    {
        'source': 'United_States_v_Connolly_2019',
        'pincite': '10',
        'statement': '"everything I have reviewed proves that the United States outsourced its investigation to Deutsche Bank and its lawyers."',
        'expected_conclusion': 'Exact Quote Mismatch'
    },
    {
        'source': 'United_States_v_Connolly_2019',
        'pincite': '9',
        'statement': 'Black was fired in early 2015 at the insistence of the New York Department of Financial Services.',
        'expected_conclusion': 'Supports At Cited Location'
    },
    {
        'source': 'United_States_v_Connolly_2019',
        'pincite': '12',
        'statement': 'The government told Deutsche Bank whom to interview and when, including directing it to interview Gavin Black.',
        'expected_conclusion': 'Supports At Cited Location'
    },
    {
        'source': 'United_States_v_Connolly_2019',
        'pincite': '11-12',
        'statement': 'The Government directed Deutsche Bank to investigate Gavin Black on its behalf and later told Deutsche Bank whom to interview and when.',
        'expected_conclusion': 'Supports At Cited Location'
    },
    {
        'source': 'United_States_v_Connolly_2019',
        'pincite': '10',
        'statement': 'The court held that the mere fact that Deutsche Bank’s investigation was outsourced by the government was sufficient by itself to establish a Fifth Amendment violation.',
        'expected_conclusion': 'Contradicts At Cited Location',
        'acceptable_conclusions': ['Contradicts, 2 Different Locations']
    },
    {
        'source': 'United_States_v_Connolly_2019',
        'pincite': '2',
        'statement': 'The CFTC fired Gavin Black in 2010.',
        'expected_conclusion': 'No Match At Cited Location, Contradicts in Alternate Location'
    },
    {
        'source': 'United_States_v_Connolly_2019',
        'pincite': '22',
        'statement': 'In United States v. Allen, the indictment was dismissed because compelled testimony reached the grand jury.',
        'expected_conclusion': 'Supports At Cited Location'
    },
    {
        'source': 'United_States_v_Connolly_2019',
        'pincite': '22',
        'statement': 'The court concluded that Black’s case was materially the same as Allen and therefore required dismissal of Black’s indictment.',
        'expected_conclusion': 'Contradicts At Cited Location',
        'acceptable_conclusions': ['Contradicts, 2 Different Locations']
    },
    # =========================================================
    # ARMBRUSTER
    # =========================================================
    {
        'source': 'United_States_v_Armbruster_2021',
        'pincite': '1',
        'statement': 'The defendants were charged with securities and wire fraud offenses.',
        'expected_conclusion': 'Supports At Cited Location'
    },
    {
        'source': 'United_States_v_Armbruster_2021',
        'pincite': '3',
        'statement': 'There was evidence that someone threatened the defendants with job loss if they refused to answer questions.',
        'expected_conclusion': 'Contradicts At Cited Location'
    },
    {
        'source': 'United_States_v_Armbruster_2021',
        'pincite': '3',
        'statement': '"there is no evidence in the record that anyone ever threatened the defendants with job loss if they did not answer questions."',
        'expected_conclusion': 'Exact Quote Match'
    },
    {
        'source': 'United_States_v_Armbruster_2021',
        'pincite': '1',
        'statement': 'The court ultimately denied the defendants’ motions to dismiss.',
        'expected_conclusion': 'Insufficient At Cited Location, Supports in Alternate Location'
    },
    {
        'source': 'United_States_v_Armbruster_2021',
        'pincite': '4',
        'statement': 'The government charged the defendants with securities and wire fraud offenses.',
        'expected_conclusion': 'No Match At Cited Location, Supports in Alternate Location'
    },
    {
        'source': 'United_States_v_Armbruster_2021',
        'pincite': '1',
        'statement': 'The court held that the defendants’ statements were compelled by the threat of losing their jobs.',
        'expected_conclusion': 'Contradicts At Cited Location',
        'acceptable_conclusions': ['Contradicts, 2 Different Locations']
    },
    {
        'source': 'United_States_v_Armbruster_2021',
        'pincite': '3',
        'statement': 'The defendants’ statements were compelled.',
        'expected_conclusion': 'Contradicts At Cited Location',
        'acceptable_conclusions': ['Contradicts, 2 Different Locations']
    },
    {
        'source': 'United_States_v_Armbruster_2021',
        'pincite': '4',
        'statement': '"the defendants motions to dismiss (R. 82, 87, 90) are granted."',
        'expected_conclusion': 'Exact Quote Mismatch'
    },
    {
        'source': 'United_States_v_Armbruster_2021',
        'pincite': '4',
        'statement': 'The court adopted the magistrate judge’s recommendation and denied the defendants’ motions to dismiss.',
        'expected_conclusion': 'Supports At Cited Location'
    },
    {
        'source': 'United_States_v_Armbruster_2021',
        'pincite': '1-4',
        'statement': 'The defendants were charged with securities and wire fraud offenses, and the court ultimately denied their motions to dismiss.',
        'expected_conclusion': 'Supports At Cited Location'
    },
    # =========================================================
    # REVLON
    # =========================================================
    {
        'source': 'Revlon_v_MacAndrews_Forbes_1986',
        'pincite': '182',
        'statement': 'Once the breakup and sale of Revlon became inevitable, the board’s duty changed from preserving the corporate entity to maximizing the company’s value for the stockholders.',
        'expected_conclusion': 'Supports At Cited Location'
    },
    {
        'source': 'Revlon_v_MacAndrews_Forbes_1986',
        'pincite': '181',
        'statement': 'The court concluded that the Rights Plan was unreasonable in relation to the threat posed.',
        'expected_conclusion': 'Contradicts At Cited Location'
    },
    {
        'source': 'Revlon_v_MacAndrews_Forbes_1986',
        'pincite': '181',
        'statement': 'The Rights Plan helped cause Pantry Pride to increase its bids and initially benefited the shareholders.',
        'expected_conclusion': 'Supports At Cited Location'
    },
    {
        'source': 'Revlon_v_MacAndrews_Forbes_1986',
        'pincite': '181',
        'statement': 'Revlon’s initial defensive tactics worked to the benefit of the shareholders.',
        'expected_conclusion': 'Supports At Cited Location',
        'acceptable_conclusions': ['Supports, 2 Different Locations']
    },
    {
        'source': 'Revlon_v_MacAndrews_Forbes_1986',
        'pincite': '184',
        'statement': 'The Revlon board ended the auction in return for very little actual improvement in the final bid.',
        'expected_conclusion': 'Supports At Cited Location'
    },
    {
        'source': 'Revlon_v_MacAndrews_Forbes_1986',
        'pincite': '185',
        'statement': 'Although the board’s initial defensive tactics benefited shareholders, the later asset-option lock-up ended the auction to the detriment of shareholders.',
        'expected_conclusion': 'Supports At Cited Location'
    },
    {
        'source': 'Revlon_v_MacAndrews_Forbes_1986',
        'pincite': '181',
        'statement': 'The Revlon board’s takeover measures benefited shareholders.',
        'expected_conclusion': 'Supports At Cited Location',
        'acceptable_conclusions': ['Supports At Pincite, Contradicted Elsewhere']
    },
    {
        'source': 'Revlon_v_MacAndrews_Forbes_1986',
        'pincite': '184',
        'statement': 'The Revlon board’s takeover measures were reasonable and benefited shareholders.',
        'expected_conclusion': 'Contradicts At Cited Location',
        'acceptable_conclusions': ['Contradicts, 2 Different Locations']
    },
    {
        'source': 'Revlon_v_MacAndrews_Forbes_1986',
        'pincite': '181',
        'statement': '"The directors\' role changed from defenders of the corporate bastion to auctioneers charged with getting the best price for the stockholders at a sale of the company."',
        'expected_conclusion': 'Exact Quote Match In Other Location'
    },
    {
        'source': 'Revlon_v_MacAndrews_Forbes_1986',
        'pincite': '181-182',
        'statement': '"The directors\' role changed from defenders of the corporate bastion to auctioneers charged with getting the best price for the stockholders at a sale of the company."',
        'expected_conclusion': 'Exact Quote Match'
    },
    {
        'source': 'Revlon_v_MacAndrews_Forbes_1986',
        'pincite': '181',
        'statement': 'Once it became apparent that Revlon was for sale, the directors’ role changed to that of auctioneers seeking the best price for shareholders.',
        'expected_conclusion': 'No Match At Cited Location, Supports in Alternate Location'
    },
    # =========================================================
    # UNOCAL
    # =========================================================
    {
        'source': 'Unocal_v_Mesa_Petroleum_1985',
        'pincite': '954-955',
        'statement': 'Directors responding to a takeover threat must show reasonable grounds for believing that a danger to corporate policy and effectiveness existed, and good faith and reasonable investigation can satisfy that burden.',
        'expected_conclusion': 'Supports At Cited Location'
    },
    {
        'source': 'Unocal_v_Mesa_Petroleum_1985',
        'pincite': '954',
        'statement': 'A Delaware corporation may deal selectively with its stockholders so long as the directors are not acting for the sole or primary purpose of entrenching themselves.',
        'expected_conclusion': 'Supports At Cited Location'
    },
    {
        'source': 'Unocal_v_Mesa_Petroleum_1985',
        'pincite': '954',
        'statement': 'Directors may selectively use corporate power for the sole purpose of entrenching themselves in office.',
        'expected_conclusion': 'Contradicts At Cited Location'
    },
    {
        'source': 'Unocal_v_Mesa_Petroleum_1985',
        'pincite': '954',
        'statement': 'Directors must show reasonable grounds for believing that a danger to corporate policy and effectiveness existed and may satisfy that burden through good faith and reasonable investigation.',
        'expected_conclusion': 'Insufficient At Cited Location, Supports in Alternate Location'
    },
    {
        'source': 'Unocal_v_Mesa_Petroleum_1985',
        'pincite': '954',
        'statement': '"We must bear in mind the inherent danger in the purchase of shares with corporate funds to remove a threat to corporate policy when a threat to control is involved."',
        'expected_conclusion': 'Exact Quote Match In Other Location'
    },
    {
        'source': 'Unocal_v_Mesa_Petroleum_1985',
        'pincite': '954-955',
        'statement': '"We must bear in mind the inherent danger in the purchase of shares with corporate funds to remove a threat to corporate policy when a threat to control is involved."',
        'expected_conclusion': 'Exact Quote Match'
    },
    {
        'source': 'Unocal_v_Mesa_Petroleum_1985',
        'pincite': '954',
        'statement': 'The Delaware Supreme Court held that Unocal’s directors were personally liable for insider trading.',
        'expected_conclusion': 'No Match Anywhere'
    },
    # =========================================================
    # KROPF ARTICLE
    # =========================================================
    {
        'source': 'Kropf_DOJ_Outsourcing_Under_Fire_Again_2023',
        'pincite': '4',
        'statement': 'The author stated that there was nothing wrong with a company taking direction from DOJ in conducting its internal investigation.',
        'expected_conclusion': 'Supports At Cited Location'
    },
    {
        'source': 'Kropf_DOJ_Outsourcing_Under_Fire_Again_2023',
        'pincite': '4',
        'statement': 'The author predicted that DOJ would probably stop encouraging corporate cooperation because cooperation has little investigative value.',
        'expected_conclusion': 'Contradicts At Cited Location'
    },
    {
        'source': 'Kropf_DOJ_Outsourcing_Under_Fire_Again_2023',
        'pincite': '3',
        'statement': 'The President and CLO requested an evidentiary hearing because many communications between DOJ and the company were oral.',
        'expected_conclusion': 'Supports At Cited Location'
    },
    {
        'source': 'Kropf_DOJ_Outsourcing_Under_Fire_Again_2023',
        'pincite': '4',
        'statement': '"There’s nothing wrong with a company taking direction from DOJ to conduct its internal investigation."',
        'expected_conclusion': 'Exact Quote Match'
    },
    {
        'source': 'Kropf_DOJ_Outsourcing_Under_Fire_Again_2023',
        'pincite': '3-4',
        'statement': 'The President and CLO requested an evidentiary hearing because many communications between DOJ and the company were oral, and the author stated that there was nothing wrong with a company taking direction from DOJ in conducting its internal investigation.',
        'expected_conclusion': 'Supports At Cited Location'
    },
    # =========================================================
    # GENERAL CITATION — SUPPORT
    # =========================================================
    {
        'source': 'United_States_v_Connolly_2019',
        'pincite': None,
        'statement': 'The court stated that the United States appeared to have outsourced its investigation to Deutsche Bank and its lawyers.',
        'expected_conclusion': 'General Citation: Supports'
    },
    {
        'source': 'United_States_v_Armbruster_2021',
        'pincite': None,
        'statement': 'The court denied the defendants’ motions to dismiss.',
        'expected_conclusion': 'General Citation: Supports'
    },
    {
        'source': 'Revlon_v_MacAndrews_Forbes_1986',
        'pincite': None,
        'statement': 'Once the sale of Revlon became inevitable, the directors’ role changed from defenders of the corporation to auctioneers seeking the best price for stockholders.',
        'expected_conclusion': 'General Citation: Supports'
    },
    {
        'source': 'Unocal_v_Mesa_Petroleum_1985',
        'pincite': None,
        'statement': 'Because directors responding to a takeover threat may act in their own interests, their actions receive enhanced judicial scrutiny before receiving business-judgment-rule protection.',
        'expected_conclusion': 'General Citation: Supports'
    },
    {
        'source': 'Kropf_DOJ_Outsourcing_Under_Fire_Again_2023',
        'pincite': None,
        'statement': 'The author stated that there is nothing inherently wrong with a company taking direction from DOJ while conducting an internal investigation.',
        'expected_conclusion': 'General Citation: Supports'
    },
    # =========================================================
    # GENERAL CITATION — CONTRADICTION
    # =========================================================
    {
        'source': 'United_States_v_Armbruster_2021',
        'pincite': None,
        'statement': 'The court held that the defendants’ statements were compelled because they faced a sufficiently certain threat of losing their jobs.',
        'expected_conclusion': 'General Citation: Contradicts'
    },
    {
        'source': 'United_States_v_Armbruster_2021',
        'pincite': None,
        'statement': 'The court granted the defendants’ motions to dismiss.',
        'expected_conclusion': 'General Citation: Contradicts'
    },
    {
        'source': 'Revlon_v_MacAndrews_Forbes_1986',
        'pincite': None,
        'statement': 'Even after the sale of Revlon became inevitable, the board’s primary duty remained preserving Revlon as an independent corporate entity.',
        'expected_conclusion': 'General Citation: Contradicts'
    },
    {
        'source': 'Unocal_v_Mesa_Petroleum_1985',
        'pincite': None,
        'statement': 'A corporate board is required to remain passive when confronted with a hostile takeover bid.',
        'expected_conclusion': 'General Citation: Contradicts'
    },
    {
        'source': 'Kropf_DOJ_Outsourcing_Under_Fire_Again_2023',
        'pincite': None,
        'statement': 'The author predicted that DOJ would stop encouraging corporate cooperation because cooperation has little investigative value.',
        'expected_conclusion': 'General Citation: Contradicts'
    },
    # =========================================================
    # GENERAL CITATION — NO MATCH
    # =========================================================
    {
        'source': 'United_States_v_Connolly_2019',
        'pincite': None,
        'statement': 'The court held that Goldman Sachs employees committed insider trading based on confidential merger information.',
        'expected_conclusion': 'General Citation: No Match'
    },
    {
        'source': 'United_States_v_Armbruster_2021',
        'pincite': None,
        'statement': 'The court determined that the defendants infringed a pharmaceutical patent.',
        'expected_conclusion': 'General Citation: No Match'
    },
    {
        'source': 'Revlon_v_MacAndrews_Forbes_1986',
        'pincite': None,
        'statement': 'The court held that Revlon was strictly liable for injuries caused by a defective consumer product.',
        'expected_conclusion': 'General Citation: No Match'
    },
    {
        'source': 'Unocal_v_Mesa_Petroleum_1985',
        'pincite': None,
        'statement': 'The court held that Unocal violated federal environmental law by contaminating groundwater.',
        'expected_conclusion': 'General Citation: No Match'
    },
    # =========================================================
    # GENERAL CITATION — INSUFFICIENT
    # =========================================================
    {
        'source': 'Kropf_DOJ_Outsourcing_Under_Fire_Again_2023',
        'pincite': None,
        'statement': 'Because the court held an evidentiary hearing and ordered supplemental briefing, the President and CLO were likely to prevail on their suppression arguments.',
        'expected_conclusion': 'General Citation: Insufficient'
    },
    {
        'source': 'Unocal_v_Mesa_Petroleum_1985',
        'pincite': None,
        'statement': 'Whenever a majority of a board consists of independent outside directors, any takeover defense adopted by the board is automatically lawful.',
        'expected_conclusion': 'General Citation: Contradicts'
    },
    # =========================================================
    # GENERAL CITATION + EXACT QUOTE
    # =========================================================
    {
        'source': 'United_States_v_Connolly_2019',
        'pincite': None,
        'statement': '"everything I have read suggests that the United States outsourced its investigation to Deutsche Bank and its lawyers."',
        'expected_conclusion': 'Exact Quote Match, No Pincite'
    },
    {
        'source': 'United_States_v_Armbruster_2021',
        'pincite': None,
        'statement': '"there is no evidence in the record that anyone ever threatened the defendants with job loss if they did not answer questions."',
        'expected_conclusion': 'Exact Quote Match, No Pincite'
    },
    # 1. Wider range containing irrelevant material should still work
    {
        'source': 'Unocal_v_Mesa_Petroleum_1985',
        'pincite': '954-956',
        'statement': (
            'Directors responding to a takeover threat must show reasonable grounds '
            'for believing that a danger to corporate policy and effectiveness existed, '
            'and good faith and reasonable investigation can satisfy that burden.'
        ),
        'expected_conclusion': 'Supports At Cited Location'
    },
    # 2. Single pincite should NOT be allowed to borrow the missing half
    {
        'source': 'Unocal_v_Mesa_Petroleum_1985',
        'pincite': '955',
        'statement': (
            'Directors responding to a takeover threat must show reasonable grounds '
            'for believing that a danger to corporate policy and effectiveness existed, '
            'and good faith and reasonable investigation can satisfy that burden.'
        ),
        'expected_conclusion': 'Insufficient With No Better Location'
    },
    # 3. General/sourcewide citation should not stitch disconnected passages together
    {
        'source': 'Unocal_v_Mesa_Petroleum_1985',
        'pincite': None,
        'statement': (
            'Directors responding to a takeover threat must show reasonable grounds '
            'for believing that a danger to corporate policy and effectiveness existed, '
            'and good faith and reasonable investigation can satisfy that burden.'
        ),
        'expected_conclusion': 'General Citation: Insufficient'
    },
    #citation with comma-separated pincites
    {
        'source': 'United_States_v_Armbruster_2021',
        'pincite': '1, 4',
        'statement': 'The defendants were charged with securities and wire fraud offenses, and the court ultimately denied their motions to dismiss.',
        'expected_conclusion': 'Supports At Cited Location'
    },
    {
        'source': 'United_States_v_Armbruster_2021',
        'pincite': '1, 4',
        'statement': (
            'The defendants were charged with securities and wire fraud offenses, '
            'the record contained no evidence that anyone threatened them with job loss '
            'if they refused to answer questions, and the court ultimately denied their '
            'motions to dismiss.'
        ),
        'expected_conclusion': 'Supports At Cited Location'
    },
    # =========================================================
    # PINCITE SET REGRESSION TESTS
    # =========================================================
    # Page 3 is inside the continuous range 1-4.
    {
        'source': 'United_States_v_Armbruster_2021',
        'pincite': '1-4',
        'statement': 'The record contained no evidence that anyone threatened the defendants with job loss if they refused to answer questions.',
        'expected_conclusion': 'Supports At Cited Location'
    },
    # Page 3 is NOT inside the discrete citation 1, 4.
    {
        'source': 'United_States_v_Armbruster_2021',
        'pincite': '1, 4',
        'statement': 'The record contained no evidence that anyone threatened the defendants with job loss if they refused to answer questions.',
        'expected_conclusion': 'No Match At Cited Location, Supports in Alternate Location'
    }

]


model_descriptions = pd.DataFrame({
    'model_shortname': [
        'MiniLM', 'E5 Base',
        'BGE', 'GTE',
        'Jina', 'Qwen',
        'E5 Mistral', 'Dinghy Law'
    ],

    'model_fullname': [
        'sentence-transformers/all-MiniLM-L6-v2',
        'intfloat/e5-base-v2',
        'BAAI/bge-base-en-v1.5',
        'thenlper/gte-base',
        'jinaai/jina-embeddings-v3-hf',
        'Qwen/Qwen3-Embedding-0.6B',
        'intfloat/e5-mistral-7b-instruct',
        'Hanno-Labs/dinghy-law-0.6b-v1'
    ],

    'backbone': ['Encoder'] * 5 + ['Decoder'] * 3,

    'Representation': ['Dense'] * 8,

    'ContrastiveTraining': [True] * 8,

    'HardNegativeTraining': [
        False, True, True, True,
        True, True, True, True
    ],

    'InstructionTraining': [
        False, False, True, False,
        False, True, True, True
    ],

    'QueryPassageTraining': [
        False, True, True, False,
        True, True, True, True
    ],

    'MultiTaskTraining': [
        False, False, True, True,
        True, True, True, False
    ]
})