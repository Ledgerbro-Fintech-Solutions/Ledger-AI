import pandas as pd
from typing import List, Optional
from backend.app.core.logging import logger


def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Clean DataFrame by stripping strings, filling NAs, and removing entirely empty rows."""
    if df is None or df.empty:
        return pd.DataFrame()

    df_clean = df.copy()
    # Strip string columns
    for col in df_clean.select_dtypes(include=['object']):
        df_clean[col] = df_clean[col].apply(lambda x: x.strip() if isinstance(x, str) else x)

    # Drop entirely empty rows
    df_clean = df_clean.dropna(how='all')
    return df_clean


def format_price_with_currency(price: Optional[float], currency: Optional[str]) -> Optional[str]:
    """Format numeric price with currency symbol."""
    if pd.isna(price) or price is None:
        return None

    if pd.isna(currency) or currency is None or str(currency).strip() == '':
        return f"{price:.2f}" if isinstance(price, (int, float)) else str(price)

    c_str = str(currency).strip()
    formatted_num = f"{price:.2f}" if isinstance(price, (int, float)) else str(price)

    # Prepend common currency symbols
    if c_str in ['$', '€', '£', '¥', '₹', 'USD', 'EUR', 'GBP', 'INR']:
        return f"{c_str}{formatted_num}"
    return f"{formatted_num} {c_str}"


def merge_dataframes_intelligently(dfs: List[pd.DataFrame]) -> pd.DataFrame:
    """Align columns and merge multiple DataFrames into a single unified table."""
    if not dfs:
        return pd.DataFrame()

    valid_dfs = [df for df in dfs if df is not None and not df.empty]
    if not valid_dfs:
        return pd.DataFrame()

    if len(valid_dfs) == 1:
        return valid_dfs[0]

    all_columns = set()
    for df in valid_dfs:
        all_columns.update(df.columns.tolist())

    aligned = []
    for df in valid_dfs:
        df_copy = df.copy()
        for col in all_columns:
            if col not in df_copy.columns:
                df_copy[col] = None
        aligned.append(df_copy[sorted(all_columns)])

    merged_df = pd.concat(aligned, ignore_index=True)
    logger.info(f"Merged {len(valid_dfs)} tables into {len(merged_df)} rows.")
    return merged_df


def reorder_and_rename_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Format prices with currency and reorder/rename columns for presentation and export."""
    if df is None or df.empty:
        return pd.DataFrame()

    df_copy = df.copy()

    # Format price columns with currency if available
    curr_col = 'currency' in df_copy.columns
    if curr_col and 'unit_price' in df_copy.columns:
        df_copy['unit_price'] = df_copy.apply(
            lambda r: format_price_with_currency(r['unit_price'], r.get('currency')), axis=1
        )
    if curr_col and 'total_price' in df_copy.columns:
        df_copy['total_price'] = df_copy.apply(
            lambda r: format_price_with_currency(r['total_price'], r.get('currency')), axis=1
        )

    if curr_col:
        df_copy = df_copy.drop('currency', axis=1, errors='ignore')

    column_mapping = {
        'source_file': 'Source File',
        'company_name': 'Vendor Name',
        'invoice_number': 'Invoice #',
        'date': 'Invoice Date',
        'due_date': 'Due Date',
        'description': 'Description',
        'item_code': 'Item Code',
        'quantity': 'Quantity',
        'unit_price': 'Unit Price',
        'total_price': 'Total Amount',
        'address': 'Vendor Address',
        'page_no': 'Page No'
    }

    desired_order = [
        'source_file', 'company_name', 'invoice_number', 'date', 'due_date',
        'description', 'item_code', 'quantity', 'unit_price', 'total_price',
        'address', 'page_no'
    ]

    available = [c for c in desired_order if c in df_copy.columns]
    additional = [c for c in df_copy.columns if c not in desired_order]
    final_cols = available + additional

    df_reordered = df_copy[final_cols]
    df_renamed = df_reordered.rename(columns={k: v for k, v in column_mapping.items() if k in df_reordered.columns})

    return df_renamed
