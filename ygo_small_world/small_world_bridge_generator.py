import json
import os
import pandas as pd
import numpy as np
from functools import cache

def sub_df(df: pd.DataFrame, column_values: list, column_name: str) -> pd.DataFrame:
    """
    Creates a subset of the given DataFrame based on specified values in a particular column.
    
    Parameters:
        df (pd.DataFrame): The input DataFrame from which the subset will be extracted.
        column_values (list): A list of values to match against the specified column to filter rows.
        column_name (str): The name of the column in which to look for the specified values.

    Returns:
        pd.DataFrame: A new DataFrame containing only the rows where the specified column contains any of the values in 'column_values'.
    """
    if column_name not in df.columns:
        raise ValueError(f"'{column_name}' is not a valid column in the DataFrame.")
    
    mask = df[column_name].isin(column_values)
    return df.loc[mask].copy()

@cache
def load_main_monsters() -> pd.DataFrame:
    """
    Loads a DataFrame containing information about all main deck monster cards from a JSON file. 
    The JSON file should contain data for all cards. This function filters for the main monster card categories.

    Returns:
        pd.DataFrame: A DataFrame containing information about all main deck monsters, 
                      including their ID, name, type, attribute, level, attack, and defense.
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))
    cardinfo_path = os.path.join(current_dir, "cardinfo.json")

    # Load the contents of cardinfo.json
    with open(cardinfo_path, "r") as file_path:
        json_all_cards = json.load(file_path)
    df_all_cards = pd.DataFrame(json_all_cards['data'])
    df_all_cards = df_all_cards.rename(columns={'type': 'category', 'race': 'type'})

    main_monster_card_category = ['Effect Monster', 'Normal Monster', 'Flip Effect Monster', 'Union Effect Monster',
                                  'Pendulum Effect Monster', 'Tuner Monster', 'Gemini Monster', 'Normal Tuner Monster',
                                  'Spirit Monster', 'Ritual Effect Monster', 'Ritual Monster', 'Toon Monster',
                                  'Pendulum Normal Monster', 'Pendulum Tuner Effect Monster', 'Pendulum Effect Ritual Monster', 'Pendulum Flip Effect Monster']
    df_main_monsters = sub_df(df_all_cards, main_monster_card_category, 'category').reset_index(drop=True) #only keep main deck monsters
    df_main_monsters = df_main_monsters[['id', 'name', 'type', 'attribute', 'level', 'atk', 'def']] #keep only relevant columns
    return df_main_monsters

def monster_names_to_df(card_names: list[str]) -> pd.DataFrame:
    """
    Converts a list of monster card names into a DataFrame containing details of those monsters.

    Parameters:
        card_names (list): List of monster card names as strings.

    Returns:
        pd.DataFrame: A DataFrame containing the information of the specified monster cards.
    """
    main_monsters = load_main_monsters()
    return sub_df(main_monsters, card_names, 'name')

# READ YDK FILES

def ydk_to_card_ids(ydk_file: str) -> list[int]:
    """
    Extracts card IDs from a given ydk (Yu-Gi-Oh Deck) file.

    Parameters:
        ydk_file (str): Path to the ydk file.

    Returns:
        list: A list of card IDs as integers.
    """
    card_ids = []
    with open(ydk_file) as f:
        lines = f.readlines()
        for line in lines:
            try:
                id = int(line)
            except:
                pass
            else:
                card_ids.append(id)
    return card_ids

def ydk_to_monster_names(ydk_file: str) -> list[str]:
    """
    Extracts the names of main deck monsters from a given ydk (Yu-Gi-Oh Deck) file.

    Parameters:
        ydk_file (str): Path to the ydk file.

    Returns:
        list: A list of names of main deck monsters present in the ydk file.
    """
    card_ids = ydk_to_card_ids(ydk_file)
    main_monsters = load_main_monsters()
    df_monsters = sub_df(main_monsters, card_ids, 'id')
    monster_names = df_monsters['name'].tolist()
    return monster_names

#### ADJACENCY MATRIX GENERATION ####

def df_to_adjacency_matrix(df_cards: pd.DataFrame, squared: bool = False) -> np.ndarray:
    """
    Creates an adjacency matrix based on Small World connections for a given DataFrame of cards.
    Two cards are considered adjacent if they have exactly one property in common from the following attributes: type, attribute, level, attack, or defense.

    Parameters:
        df_cards (pd.DataFrame): DataFrame containing information about the cards.
        squared (bool, optional): If True, the adjacency matrix is squared; default is False.

    Returns:
        np.array: An adjacency matrix representing the connections between cards.
    """
    df_cards = df_cards[['type', 'attribute', 'level', 'atk', 'def']]
    array_cards = df_cards.to_numpy()
    num_cards = len(df_cards)
    adjacency_matrix = np.zeros((num_cards, num_cards))
    for i in range(num_cards):
        card_similarities = array_cards==array_cards[i]
        similarity_measure = card_similarities.astype(int).sum(axis=1)
        adjacency_matrix[:,i] = (similarity_measure==1).astype(int) #indicates where there is exactly one similarity
    if squared:
        adjacency_matrix = np.linalg.matrix_power(adjacency_matrix, 2)
    return adjacency_matrix

def names_to_adjacency_matrix(card_names: list[str], squared: bool = False) -> np.ndarray:
    """
    Creates an adjacency matrix based on Small World connections for a list of monster card names.

    Parameters:
        card_names (list): List of monster card names.
        squared (bool, optional): If True, the adjacency matrix is squared; default is False.

    Returns:
        ndarray: An adjacency matrix representing the connections between the named cards.
    """
    df_cards = monster_names_to_df(card_names)
    adjacency_matrix = df_to_adjacency_matrix(df_cards, squared=squared)
    return adjacency_matrix

def names_to_labeled_adjacency_matrix(card_names: list[str], squared: bool = False) -> pd.DataFrame:
    """
    Creates a labeled adjacency matrix DataFrame based on Small World connections for a given list of monster names.

    Parameters:
        card_names (list): List of monster names.
        squared (bool, optional): If True, the adjacency matrix is squared; default is False.

    Returns:
        pd.DataFrame: A labeled adjacency matrix with both row and column names corresponding to the monster names.
    """
    adjacency_matrix = names_to_adjacency_matrix(card_names, squared=squared)
    df_adjacency_matrix = pd.DataFrame(adjacency_matrix, index=card_names, columns=card_names)
    return df_adjacency_matrix

def ydk_to_labeled_adjacency_matrix(ydk_file: str, squared: bool = False) -> pd.DataFrame:
    """
    Creates a labeled adjacency matrix DataFrame based on Small World connections from a given ydk (Yu-Gi-Oh Deck) file.

    Parameters:
        ydk_file (str): Path to the ydk file containing the deck information.
        squared (bool, optional): If True, the adjacency matrix is squared; default is False.

    Returns:
        pd.DataFrame: A labeled adjacency matrix with both row and column names corresponding to the names of monsters in the ydk file.
    """
    card_names = ydk_to_monster_names(ydk_file)
    df_adjacency_matrix = names_to_labeled_adjacency_matrix(card_names, squared=squared)
    return df_adjacency_matrix

#### BRIDGE FINDING ####

def find_best_bridges(deck_monster_names: list[str], required_target_names: list[str] = []) -> pd.DataFrame:
    """
    Identifies the best bridges (monsters) that connect the most cards in the deck via Small World
    and connect to all the required targets.

    Parameters:
        deck_monster_names (list): A list of monster names in the deck.
        required_target_names (list, optional): A list of monster names that must be connected to the bridges via Small World.
          Default is an empty list.

    Returns:
        DataFrame: A Pandas DataFrame containing details of the best bridges including bridge score, number of connections,
          name, type, attribute, level, attack, and defense. If no bridges meet the requirements, prints a message and returns None.
    """
    main_monsters = load_main_monsters()
    sw_adjacency_matrix = df_to_adjacency_matrix(main_monsters) #small world adjacency array of all cards
    deck_monster_names = list(set(deck_monster_names) | set(required_target_names)) #union names so required_target_names is a subset of deck_monster_names
    deck_indices = sub_df(main_monsters, deck_monster_names, 'name').index
    required_indices = sub_df(main_monsters, required_target_names, 'name').index #indices of required targets

    num_required_targets = len(required_target_names) #number of cards required to connect with one bridge

    required_monster_matrix = sw_adjacency_matrix[required_indices, :] #array corresponding to required connection monsters by all monsters
    num_bridges_to_required_cards = required_monster_matrix.sum(axis=0) #number of required connections satisfied by all monsters
    required_bridge_mask = num_bridges_to_required_cards==num_required_targets
    df_bridges = main_monsters[required_bridge_mask].copy() #data frame of monsters connecting all required targets
    required_bridge_indices = df_bridges.index #indices of monsters that satisfy all required connections
    if len(df_bridges)==0:
        raise ValueError(f'There are no monsters that bridge all required targets.')
    #subset of adjacency matrix corresponding to (deck monsters) by (monsters with connections to the required cards)
    bridge_matrix = sw_adjacency_matrix[deck_indices,:][:,required_bridge_indices]

    num_deck_bridges = bridge_matrix.sum(axis=0)
    df_bridges['number_of_connections'] = num_deck_bridges

    #calculate bridge score = num non-zero entries in square of adjacency matrix if bridge was included divided by square of num cards in deck + 1
    adjacency_matrix = names_to_adjacency_matrix(deck_monster_names)
    adjacency_matrix_squared = names_to_adjacency_matrix(deck_monster_names, squared = True)

    num_deck_cards = bridge_matrix.shape[0]
    i,j = np.mgrid[0:num_deck_cards, 0:num_deck_cards]
    outer_product_tensor = bridge_matrix[i] * bridge_matrix[j] #outer product of connection vectors
    deck_connection_tensor = outer_product_tensor + adjacency_matrix_squared[:, :, np.newaxis] #A^2 + x(x.T) for all connection vectors x
    deck_connectivity = deck_connection_tensor.astype(bool).astype(int).sum(axis=(0,1)) #number of non-zero elements in each slice

    bridge_connection_matrix = adjacency_matrix @ bridge_matrix
    bridge_connectivity = bridge_connection_matrix.astype(bool).astype(int).sum(axis=0) #num non-zero elements in each row

    bridge_score = (deck_connectivity + 2*bridge_connectivity + 1)/((num_deck_cards+1)**2) #formula derived from block matrix multiplication
    df_bridges['bridge_score'] = bridge_score

    #assemble df
    df_bridges = df_bridges[df_bridges['number_of_connections'] > 0]
    df_bridges = df_bridges[['bridge_score', 'number_of_connections', 'name', 'type', 'attribute', 'level', 'atk', 'def']]  #reorder columns
    df_bridges = df_bridges.sort_values(by=['bridge_score', 'number_of_connections', 'name'], ascending=[False, False, True]).reset_index(drop=True) #reorder rows
    return df_bridges

def find_best_bridges_from_ydk(ydk_file: str) -> pd.DataFrame:
    """
    Identifies the best bridges that connect the most cards in the deck from a given ydk (Yu-Gi-Oh Deck) file.

    Parameters:
        ydk_file (str): Path to the ydk file of the deck.

    Returns:
        DataFrame: A Pandas DataFrame containing details of the best bridges. The same as returned by `find_best_bridges`.
    """
    deck_monster_names = ydk_to_monster_names(ydk_file)
    df_bridges = find_best_bridges(deck_monster_names)
    return df_bridges