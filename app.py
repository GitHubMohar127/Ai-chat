import streamlit as st
import pandas as pd

from src.product_search import search_products
from src.response_handler import get_ai_response


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Hindcon Product Assistant",
    page_icon="📘",
    layout="centered"
)


# ============================================================
# LOAD DATA
# ============================================================

@st.cache_data
def load_data():

    return pd.read_excel(
        "data/hindcon_master_dataset.xlsx"
    )


try:

    df = load_data()

except Exception as e:

    st.error(
        f"Unable to load the product dataset: {e}"
    )

    st.stop()


# ============================================================
# HEADER
# ============================================================

st.title(
    "📘 Hindcon Product Assistant"
)

st.caption(
    "Search for a Hindcon product to find its available "
    "Technical Data Sheet (TDS) and Material Safety Data Sheet (MSDS)."
)


# ============================================================
# SESSION STATE
# ============================================================

if "messages" not in st.session_state:

    st.session_state.messages = []


# ============================================================
# CLEAN DOCUMENT LINK
# ============================================================

def clean_document_link(value):

    if pd.isna(value):

        return None

    value = str(
        value
    ).strip()

    if not value:

        return None

    unavailable_values = {
        "nan",
        "none",
        "null",
        "tbd",
        "n/a",
        "na",
        "not available",
        "not found",
        "tds not found",
        "msds not found",
        "tds unavailable",
        "msds unavailable"
    }

    if value.lower() in unavailable_values:

        return None

    if not (
        value.lower().startswith(
            "http://"
        )
        or
        value.lower().startswith(
            "https://"
        )
    ):

        return None

    return value


# ============================================================
# DISPLAY MESSAGE
# ============================================================

def display_message(message):

    role = message.get(
        "role",
        "assistant"
    )

    with st.chat_message(role):

        # ====================================================
        # USER MESSAGE
        # ====================================================

        if role == "user":

            st.markdown(
                message.get(
                    "content",
                    ""
                )
            )

            return


        # ====================================================
        # ASSISTANT MESSAGE TYPE
        # ====================================================

        message_type = message.get(
            "type",
            "text"
        )


        # ====================================================
        # NORMAL TEXT
        # ====================================================

        if message_type == "text":

            st.markdown(
                message.get(
                    "content",
                    ""
                )
            )


        # ====================================================
        # SINGLE PRODUCT
        # ====================================================

        elif message_type == "product":

            product_name = message.get(
                "product_name",
                "Product"
            )

            tds_link = message.get(
                "tds_link"
            )

            msds_link = message.get(
                "msds_link"
            )

            st.markdown(
                f"**📦 {product_name}**"
            )

            col1, col2 = st.columns(
                2
            )


            # ------------------------------------------------
            # TDS
            # ------------------------------------------------

            with col1:

                if tds_link:

                    st.link_button(
                        "📄 TDS",
                        tds_link,
                        use_container_width=True
                    )

                else:

                    st.caption(
                        "TDS: Not Available"
                    )


            # ------------------------------------------------
            # MSDS
            # ------------------------------------------------

            with col2:

                if msds_link:

                    st.link_button(
                        "🛡️ MSDS",
                        msds_link,
                        use_container_width=True
                    )

                else:

                    st.caption(
                        "MSDS: Not Available"
                    )


        # ====================================================
        # MULTIPLE PRODUCTS
        # ====================================================

        elif message_type == "multiple_products":

            st.markdown(
                message.get(
                    "content",
                    "Multiple products found:"
                )
            )

            products = message.get(
                "products",
                []
            )

            # ------------------------------------------------
            # CREATE CLICKABLE PRODUCT BUTTONS
            # ------------------------------------------------

            for index, product_name in enumerate(
                products,
                start=1
            ):

                if st.button(
                    f"{index}. {product_name}",
                    key=f"product_select_{message.get('id', 'msg')}_{index}",
                    use_container_width=True
                ):

                    # ----------------------------------------
                    # Search the selected product directly
                    # No Gemini call is required here.
                    # ----------------------------------------

                    selected_matches = search_products(
                        df,
                        product_name
                    )


                    # ----------------------------------------
                    # If exactly one product is found
                    # ----------------------------------------

                    if len(selected_matches) == 1:

                        selected_product = (
                            selected_matches.iloc[0]
                        )

                        selected_product_name = str(
                            selected_product.get(
                                "Product_Name",
                                product_name
                            )
                        ).strip()

                        selected_tds_link = (
                            clean_document_link(
                                selected_product.get(
                                    "TDS_Link"
                                )
                            )
                        )

                        selected_msds_link = (
                            clean_document_link(
                                selected_product.get(
                                    "MSDS_Link"
                                )
                            )
                        )


                        # ------------------------------------
                        # Add selected product as user message
                        # ------------------------------------

                        st.session_state.messages.append(
                            {
                                "role": "user",
                                "type": "text",
                                "content": selected_product_name
                            }
                        )


                        # ------------------------------------
                        # Add product result
                        # ------------------------------------

                        st.session_state.messages.append(
                            {
                                "role": "assistant",
                                "type": "product",
                                "product_name": selected_product_name,
                                "tds_link": selected_tds_link,
                                "msds_link": selected_msds_link
                            }
                        )


                        # ------------------------------------
                        # Refresh the application
                        # ------------------------------------

                        st.rerun()


                    # ----------------------------------------
                    # Safety fallback
                    # ----------------------------------------

                    else:

                        st.session_state.messages.append(
                            {
                                "role": "assistant",
                                "type": "text",
                                "content": (
                                    "Sorry, I could not uniquely "
                                    "identify that product. "
                                    "Please try searching for the "
                                    "full product name."
                                )
                            }
                        )

                        st.rerun()


# ============================================================
# DISPLAY CHAT HISTORY
# ============================================================

for message in st.session_state.messages:

    display_message(
        message
    )


# ============================================================
# USER INPUT
# ============================================================

user_message = st.chat_input(
    "Search for a Hindcon product..."
)


# ============================================================
# PROCESS USER MESSAGE
# ============================================================

if user_message:

    # ========================================================
    # STEP 1
    # SAVE USER MESSAGE
    # ========================================================

    st.session_state.messages.append(
        {
            "role": "user",
            "type": "text",
            "content": user_message
        }
    )


    # ========================================================
    # STEP 2
    # ASK GEMINI TO UNDERSTAND THE MESSAGE
    # ========================================================

    ai_response = get_ai_response(
        user_message
    )


    # ========================================================
    # STEP 3
    # GREETING / CASUAL / INVALID
    # ========================================================

    if ai_response["type"] == "text":

        st.session_state.messages.append(
            {
                "role": "assistant",
                "type": "text",
                "content": ai_response["message"]
            }
        )

        st.rerun()


    # ========================================================
    # STEP 4
    # PRODUCT SEARCH
    # ========================================================

    if ai_response["type"] == "product_search":

        # ----------------------------------------------------
        # Gemini extracted the actual product search text.
        #
        # Example:
        #
        # "Give me the TDS of Hind Crystel Seal"
        #
        # becomes:
        #
        # "Hind Crystel Seal"
        # ----------------------------------------------------

        search_query = ai_response.get(
            "search_query",
            user_message
        )

        if not search_query:

            search_query = user_message


        try:

            results = search_products(
                df,
                search_query
            )


            # =================================================
            # NO PRODUCT FOUND
            # =================================================

            if results.empty:

                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "type": "text",
                        "content": (
                            "Sorry, I could not find a matching "
                            "Hindcon product. Please check the "
                            "product name or try another spelling."
                        )
                    }
                )


            # =================================================
            # ONE PRODUCT FOUND
            # =================================================

            elif len(results) == 1:

                product = results.iloc[0]


                product_name = str(
                    product.get(
                        "Product_Name",
                        "Product"
                    )
                ).strip()


                tds_link = clean_document_link(
                    product.get(
                        "TDS_Link"
                    )
                )


                msds_link = clean_document_link(
                    product.get(
                        "MSDS_Link"
                    )
                )


                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "type": "product",
                        "product_name": product_name,
                        "tds_link": tds_link,
                        "msds_link": msds_link
                    }
                )


            # =================================================
            # MULTIPLE PRODUCTS
            # =================================================

            else:

                product_names = (
                    results[
                        "Product_Name"
                    ]
                    .dropna()
                    .astype(str)
                    .str.strip()
                    .drop_duplicates()
                    .tolist()
                )


                # ---------------------------------------------
                # Give this message a unique ID.
                #
                # This prevents Streamlit button-key
                # conflicts if multiple result messages exist.
                # ---------------------------------------------

                message_id = (
                    f"multiple_{len(st.session_state.messages)}"
                )


                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "type": "multiple_products",
                        "content": (
                            "I found multiple matching products. "
                            "Please specify the product name from "
                            "the list below."
                        ),
                        "products": product_names,
                        "id": message_id
                    }
                )


        except Exception as error:

            print(
                "Product search error:",
                error
            )

            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "type": "text",
                    "content": (
                        "An error occurred while searching "
                        "for the product."
                    )
                }
            )


        # ====================================================
        # REFRESH
        # ====================================================

        st.rerun()