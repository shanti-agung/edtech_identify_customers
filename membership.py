"""

A module for identifying new members using IPEDS data

Contributor: Shanti Agung

"""

import pandas as pd
import numpy as np

def gen_ids_members(file_name):
    """Generate IPEDS ids of current members
    
    file_name: a string, name of the txt file containing IPEDS ids
    and names of current members
    Return a data frame
    """
    df = pd.read_csv(file_name, delimiter = "\t")
    ids_raw = df[['IPEDS_UnitID']]
    ids_raw = ids_raw.rename(columns={'IPEDS_UnitID':'UnitID'})
    ids_df = ids_raw.drop_duplicates()
    return ids_df
    
    
def gen_ids_all(file_name):
    """Generate IPDES ids of qualifying universities
    
    file_name: a string, the name of csv file downloaded from IPEDS
    Return a data frame
    """
    raw_df = pd.read_csv(file_name)
    
    # qualifying criteria: non-profit
    # variable at IPEDS: 'Institutional control or affiliation (IC2020)'
    col_name = 'Institutional control or affiliation (IC2020)'
    is_1 = raw_df[col_name] == 1 # public
    is_3 = raw_df[col_name] == 3 # private not-for-profit (no religious affiliation)
    is_4 = raw_df[col_name] == 4 # private not-for-profit (religious affiliation)
    is_non_profit = is_1 | is_3 | is_4
    
    # qualifying criteria: undergraduate degree-granting
    # variable at IPEDS: 'Undergraduate offering (HD2020)'
    col_name = 'Undergraduate offering (HD2020)'
    is_undergraduate = raw_df[col_name] == 1 # Yes
    
    # qualifying criteria: active
    # variable at IPEDS: 'Institution is active in current year (HD2020)'
    col_name = 'Institution is active in current year (HD2020)'
    is_active = raw_df[col_name] == 1 # Yes
    
    # create qualifying condition
    meet_criteria = is_non_profit & is_undergraduate & is_active
    
    ids_df = raw_df[meet_criteria][['UnitID']]
    return ids_df
    

def gen_ids_nonmembers(ids_all, ids_members):
    """Generate IPEDS ids of non-members
    
    ids_all: a data frame, listing ids of all qualifying universities
    ids_members: a data frame, listing ids of members
    Return a data frame
    """
    tag_ids = ids_all.merge(ids_members, on='UnitID', how='left', indicator = True)
    id_list = tag_ids.loc[tag_ids['_merge'] == 'left_only', 'UnitID']
    ids_df = ids_all[ids_all['UnitID'].isin(id_list)]
    return ids_df
    
    
def compute_market_share(ids_all, ids_members):
    """Calculate market share
    
    ids_all: a data frame, listing ids of all qualifying universities
    ids_members: a data frame, listing ids of members
    Return a float  
    """
    tag_ids = ids_all.merge(ids_members, on='UnitID', how='left', indicator = True)
    num_members = tag_ids['_merge'].value_counts(dropna = False)[1]
    num_institutions = tag_ids.shape[0]
    market_share = (num_members/num_institutions) * 100
    return market_share
    
    
def subset(file_name, ids, var_list):
    """Subset raw IPEDS data frame
    
    file_name: a string, the name of csv file downloaded from IPEDS
    ids: a data frame, containing ids of universities to subset
    var_list: a list, containing IPEDS variable names to subset
    Return a data frame
    """
    raw_df = pd.read_csv(file_name)
    subset_df = raw_df.merge(ids, on='UnitID', how='inner')[var_list]
    return subset_df
    
    
def gen_proportions(df, col_dict):
    """Generate columns of proportions
    
    df: a data frame, containing IPEDS variables
    col_dict: a dictionary, keys are IPEDS variable names (string)
    and values are new proportion variable names (string)
    Return a data frame
    """
    total = 0
    # calculate total
    for key in col_dict.keys():
        total += df[key]
    # calculate proportions
    for key,value in col_dict.items():
        df[value] = df[key]/total
    return df
    
    
def gen_blau_index(df, p_list):
    """Calculate Blau diversity index
    
    df: a data frame
    p_list, a list, containing proportion variable names (string)
    Return a column (a series)
    """
    D = 0  
    for p in p_list:
        D += df[p]**2
    blau_index = 1 - D
    return blau_index


def standardized(df, a_var):
    """Standardized a variable
    
    df: a data frame
    a_var: a string, a variable name in the data frame
    Return a column (a series)    
    """
    mean_var = np.mean(df[a_var])
    std_var = np.std(df[a_var])
    standardized_var = (df[a_var] - mean_var) / std_var
    return standardized_var
    
    
def gen_standardized_cols(df, col_dict):
    """Generate columns of standardized variables
    
    df: a data frame
    col_dict: a dictionary, keys are variable names (string)
    and values are new standardized variable names (string)
    Return a data frame
    """
    for key, value in col_dict.items():
        df[value] = standardized(df, key)
    return df
    
    
def compute_need_scores(df, col_dict, var_flip):
    """Calculate need scores
    
    df: a data frame
    col_dict: a dictionary, keys are variable names (string)
    and values are new standardized variable names (string)
    var_flip: a list, containing variable names (string) which signs must be flipped
    Return a column (a series) 
    """
    # standardized relevant variables
    df = gen_standardized_cols(df, col_dict)
    
    # flip signs
    # for gender and race diversity -- lower diversity means higher needs and vice versa
    for item in var_flip:
    	df[item] = -df[item]
    
    # calculate need scores
    vars_scaled = list(col_dict.values())
    df['need_score'] = df[vars_scaled].sum(axis=1)
    
    return df
    
    
def tag_membership(ids_all, ids_members):
    """Generate a column of membership status
    
    ids_all: a data frame, listing ids of all qualifying universities
    ids_members: a data frame, listing ids of members
    Return a data frame
    """
    tag_ids = ids_all.merge(ids_members, on='UnitID', how='left', indicator = True)
    condition = tag_ids['_merge'] == 'left_only'
    tag_ids.loc[condition, 'membership_status'] = 'non_member'
    tag_ids.loc[~condition, 'membership_status'] = 'member'
    df = tag_ids[['UnitID', 'membership_status']]
    return df


         
   
