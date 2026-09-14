import re
import pandas as pd
from rapidfuzz import fuzz


# ============================================================
# NORMALIZE TEXT
# ============================================================

def normalize_text(text):

    if not isinstance(text, str):
        return ""

    text = text.lower()

    text = text.replace(
        "–",
        "-"
    )

    text = text.replace(
        "—",
        "-"
    )

    text = re.sub(
        r"[^a-z0-9\s-]",
        " ",
        text
    )

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


# ============================================================
# SEARCH PRODUCTS
# ============================================================

def search_products(
    df,
    query,
    fuzzy_threshold=85
):

    if not query or not query.strip():

        return pd.DataFrame(
            columns=df.columns
        )


    normalized_query = normalize_text(
        query
    )


    if not normalized_query:

        return pd.DataFrame(
            columns=df.columns
        )


    search_df = df.copy()


    search_df["_normalized_name"] = (
        search_df["Product_Name"]
        .fillna("")
        .astype(str)
        .apply(normalize_text)
    )


    # ========================================================
    # REMOVE EMPTY PRODUCT NAMES
    # ========================================================

    search_df = search_df[
        search_df["_normalized_name"] != ""
    ]


    # ========================================================
    # EXACT MATCH
    # ========================================================

    exact_matches = search_df[
        search_df["_normalized_name"]
        == normalized_query
    ].copy()


    if not exact_matches.empty:

        exact_matches = exact_matches.drop_duplicates(
            subset=["_normalized_name"],
            keep="first"
        )

        return exact_matches.drop(
            columns=["_normalized_name"],
            errors="ignore"
        ).reset_index(
            drop=True
        )


    # ========================================================
    # PARTIAL MATCH
    # ========================================================

    partial_matches = search_df[
        search_df["_normalized_name"].str.contains(
            normalized_query,
            regex=False,
            na=False
        )
    ].copy()


    if not partial_matches.empty:

        partial_matches = partial_matches.drop_duplicates(
            subset=["_normalized_name"],
            keep="first"
        )

        return partial_matches.drop(
            columns=["_normalized_name"],
            errors="ignore"
        ).reset_index(
            drop=True
        )


    # ========================================================
    # FUZZY MATCH
    # ========================================================

    fuzzy_matches = []


    for index, row in search_df.iterrows():

        product_name = row[
            "_normalized_name"
        ]


        if not product_name:
            continue


        # -----------------------------------------------
        # Whole-name similarity
        # -----------------------------------------------

        ratio = fuzz.ratio(
            normalized_query,
            product_name
        )


        # -----------------------------------------------
        # Partial similarity
        # -----------------------------------------------

        partial_ratio = fuzz.partial_ratio(
            normalized_query,
            product_name
        )


        # -----------------------------------------------
        # Token similarity
        # -----------------------------------------------

        token_ratio = fuzz.token_set_ratio(
            normalized_query,
            product_name
        )


        # -----------------------------------------------
        # Use strongest score
        # -----------------------------------------------

        score = max(
            ratio,
            partial_ratio,
            token_ratio
        )


        # -----------------------------------------------
        # Short queries need stronger matching
        # -----------------------------------------------

        if len(normalized_query) <= 5:

            required_score = 92

        elif len(normalized_query) <= 10:

            required_score = 88

        else:

            required_score = fuzzy_threshold


        if score >= required_score:

            fuzzy_matches.append(
                (
                    index,
                    score
                )
            )


    # ========================================================
    # NO FUZZY MATCH
    # ========================================================

    if not fuzzy_matches:

        return pd.DataFrame(
            columns=df.columns
        )


    # ========================================================
    # CREATE RESULT
    # ========================================================

    fuzzy_df = search_df.loc[
        [
            item[0]
            for item in fuzzy_matches
        ]
    ].copy()


    score_map = {
        index: score
        for index, score
        in fuzzy_matches
    }


    fuzzy_df["_match_score"] = (
        fuzzy_df.index.map(
            score_map
        )
    )


    fuzzy_df = fuzzy_df.sort_values(
        by="_match_score",
        ascending=False
    )


    # ========================================================
    # REMOVE DUPLICATE PRODUCT NAMES
    # ========================================================

    fuzzy_df = fuzzy_df.drop_duplicates(
        subset=["_normalized_name"],
        keep="first"
    )


    # ========================================================
    # REMOVE INTERNAL COLUMNS
    # ========================================================

    fuzzy_df = fuzzy_df.drop(
        columns=[
            "_normalized_name",
            "_match_score"
        ],
        errors="ignore"
    )


    return fuzzy_df.reset_index(
        drop=True
    )