import json
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import networkx as nx
import requests
from functools import cache
from PIL import Image
from io import BytesIO
from . import small_world_bridge_generator as sw

class Settings:
    def __init__(self):
        self.card_size = 624
        self.max_pixel_brightness = 255

default_settings = Settings()

def names_to_image_urls(card_names: list[str]) -> list[str]:
    """
    Retrieves the URLs of the images corresponding to the given card names.

    Parameters:
        card_names (list): A list of card names.

    Returns:
        list: A list of URLs corresponding to the card images.
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))
    cardinfo_path = os.path.join(current_dir, "cardinfo.json")

    # Load the contents of cardinfo.json
    with open(cardinfo_path, "r") as file_path:
        json_all_cards = json.load(file_path)
    df_all_cards = pd.DataFrame(json_all_cards['data']) #dataframe of all cards to get image links

    df_deck_images = sw.sub_df(df_all_cards, card_names, 'name')
    df_deck_images['card_images'] = df_deck_images['card_images'].apply(lambda x: x[0]['image_url_cropped'])
    urls = df_deck_images['card_images'].tolist()
    return urls

@cache
def load_image(url: str) -> np.ndarray:
    """
    Loads an image from a given URL.

    Parameters:
        url (str): The URL of the image.

    Returns:
        ndarray: A NumPy array representing the image.
    """
    res = requests.get(url)
    imgage = np.array(Image.open(BytesIO(res.content)))
    return imgage

def load_images(urls: list[str]) -> list[np.ndarray]:
    """
    Loads multiple images from a list of URLs.

    Parameters:
        urls (list): A list of URLs of the images.

    Returns:
        list: A list of NumPy arrays representing the images.
    """
    images = []
    for url in urls:
        image = load_image(url)
        images.append(image)
    return images

def normalize_images(images: list[np.ndarray], settings=default_settings) -> list[np.ndarray]:
    """
    Normalizes a list of images to a standard size.

    Parameters:
        images (list): A list of NumPy arrays representing the images.
        settings (Settings, optional): An instance of the Settings class which provides
                                        `card_size` as the size of the card and
                                        `max_pixel_brightness` as the maximum value for pixel brightness.

    Returns:
        list: A list of normalized images.
    """
    card_size = settings.card_size
    max_pixel_brightness = settings.max_pixel_brightness
    normalized_images = []
    for image in images:
        image_length = image.shape[0]
        image_width = image.shape[1]
        normalized_image = np.ones([card_size, card_size, 3])*max_pixel_brightness
        #covering cases when image is too small
        if image_length < card_size and image_width < card_size: #case when length & width are too small
            normalized_image[:image_length, :image_width, :] = image
        elif image_length < card_size: #case when only length is too small
            normalized_image[:image_length, :, :] = image[:, :card_size, :]
        elif image_width < card_size: #case when only width is too small
            normalized_image[:, :image_width, :] = image[:card_size, :, :]
        else: #case when image is same size or too big
            normalized_image = image[:card_size, :card_size, :]
        normalized_image = normalized_image.astype(np.uint8)
        normalized_images.append(normalized_image)
    return normalized_images

def names_to_images(card_names: list[str]) -> list[np.ndarray]:
    """
    Converts a list of card names to normalized images.

    Parameters:
        card_names (list): A list of card names.

    Returns:
        list: A list of normalized images.
    """
    urls = names_to_image_urls(card_names)
    images = load_images(urls)
    normalized_images = normalize_images(images)
    return normalized_images

#### CREATE GRAPH IMAGE ####

def save_images(file_name: str) -> None:
    """
    Saves images to the 'images' folder in the current directory.

    Parameters:
        file_name (str): The name of the file to save.
    """
    folder_name = "images"
    #create folder
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)
    current_dir = os.getcwd()
    image_path = os.path.join(current_dir, folder_name, file_name)
    plt.savefig(image_path, dpi=450, bbox_inches='tight')


def matrix_to_graph_image(adjacency_matrix: np.ndarray, card_images: list[np.ndarray]) -> None:
    """
    Converts an ajacency matrix into a graph image visualization and saves it.

    Parameters:
        adjacency_matrix (ndarray): A NumPy array representing the adjacency matrix.
        card_images (list): A list of ndarray images corresponding to the nodes.
    """
    G = nx.from_numpy_array(adjacency_matrix)
    for i, card in enumerate(card_images):
        G.nodes[i]['image'] = card #asigns image to each node

    pos = nx.circular_layout(G)

    fig = plt.figure(figsize=(5, 5))
    ax = plt.subplot(111)
    ax.set_aspect('equal')
    nx.draw_networkx_edges(G, pos, ax=ax, width=1.3),

    plt.xlim(-1, 1)
    plt.ylim(-1, 1)

    trans = ax.transData.transform
    trans2 = fig.transFigure.inverted().transform

    num_cards = len(card_images)
    piesize = -0.003*num_cards+0.15 #image size is a linear function of the number of cards
    p2 = piesize/2.0
    for n in G:
        xx, yy = trans(pos[n]) #figure coordinates
        xa, ya = trans2((xx, yy)) #axes coordinates
        a = plt.axes([xa-p2, ya-p2, piesize, piesize])
        a.set_aspect('equal')
        a.imshow(G.nodes[n]['image'])
        a.axis('off')
    ax.axis('off')

    save_images('small-wolrd-graph.png')
    plt.show()

def names_to_graph_image(card_names: list[str]) -> None:
    """
    Converts a list of card names into a graph image visualization and saves it.

    Parameters:
        card_names (list): A list of card names.
    """
    card_images = names_to_images(card_names)
    df_deck = sw.monster_names_to_df(card_names).reset_index(drop=True)
    adjacency_matrix = sw.df_to_adjacency_matrix(df_deck)
    matrix_to_graph_image(adjacency_matrix, card_images)

def ydk_to_graph_image(ydk_file: str) -> None:
    """
    Converts a ydk (Yu-Gi-Oh Deck) file into a graph image visualization and saves it.

    Parameters:
        ydk_file (str): Path to the ydk file of the deck.
    """
    card_names = sw.ydk_to_monster_names(ydk_file)
    names_to_graph_image(card_names)

#### CREATE MATRIX IMAGE ####

def matrix_to_image(adjacency_matrix: np.ndarray, settings=default_settings) -> np.ndarray:
    '''
    Generate the matrix subimage of the full matrix imageas an np.ndarray of size N x N x 3.
    N is CARD_SIZE*num_cards. The third dimension is for the color channels.

    Parameters:
        adjacency_matrix (ndarray): A NumPy array representing the adjacency matrix.
        settings (Settings, optional): An instance of the Settings class which provides
                                        `card_size` as the size of the card and
                                        `max_pixel_brightness` as the maximum value for pixel brightness.
    Returns:
        ndarray: An image of the submatrix
    '''
    card_size = settings.card_size
    max_pixel_brightness = settings.max_pixel_brightness
    num_cards = adjacency_matrix.shape[0]
    #check that the adjacency matrix is square
    if num_cards != adjacency_matrix.shape[1]:
        raise ValueError("The adjacency matrix must be square.")
    
    matrix_subimage_size = card_size*num_cards #size of matrix subimage, not including card images
    matrix_subimage = np.ones((matrix_subimage_size, matrix_subimage_size, 3))*max_pixel_brightness

    matrix_maximum = np.max(adjacency_matrix)

    #color in cells
    for i in range(num_cards):
        #specify the vertical range of the region in the image corresponding to the adjacency matrix entry
        vertical_min = i*card_size
        vertical_max = (i+1)*card_size
        for j in range(num_cards):
            #specify the horizohntal range of the region in the image corresponding to the adjacency matrix entry
            horizontal_min = j*card_size
            horizontal_max = (j+1)*card_size
            scaled_matrix_value = adjacency_matrix[i, j]/matrix_maximum
            matrix_subimage[vertical_min:vertical_max, horizontal_min:horizontal_max, :] = max_pixel_brightness*(1-scaled_matrix_value)
    return matrix_subimage


def cards_and_matrix_to_image(adjacency_matrix: np.ndarray, card_images: list[np.ndarray], settings=default_settings) -> None:
    """
    Converts an adjacency matrix into an image and saves it.

    Parameters:
        adjacency_matrix (ndarray): A NumPy array representing the ajdacency matrix.
        card_images (list): A list of ndarray images corresponding to the nodes.
        settings (Settings, optional): An instance of the Settings class which provides
                                        `card_size` as the size of the card and
                                        `max_pixel_brightness` as the maximum value for pixel brightness.
    """
    card_size = settings.card_size
    max_pixel_brightness = settings.max_pixel_brightness
    num_cards = len(card_images)

    #check that number of cards equals each dimension of the adjacency matrix
    if not (num_cards == adjacency_matrix.shape[0] == adjacency_matrix.shape[1]):
        raise ValueError("The number of card images must equal to each dimension of the adjacency matrix.")

    #If the adjacency matrix is all zeros, then there are no Small World connections between cards.
    adjacency_max = np.max(adjacency_matrix)
    if adjacency_max==0:
        raise ValueError("There are no Small World connections between cards.")

    #create matrix subimage
    matrix_subimage = matrix_to_image(adjacency_matrix)

    #assemble full image
    full_image_size = card_size*(num_cards+1)
    full_image = np.ones((full_image_size,full_image_size,3))*max_pixel_brightness

    vertical_cards = np.concatenate(card_images, axis=1) #concatenated images horizontally
    horizontal_cards = np.concatenate(card_images, axis=0) #concatenated images vertically

    full_image[card_size:, 0:card_size, :] = horizontal_cards
    full_image[0:card_size, card_size:, :] = vertical_cards
    full_image[card_size:, card_size:, :] = matrix_subimage

    full_image = full_image.astype(np.uint8)

    #create figure
    fig = plt.imshow(full_image)
    ax = plt.subplot(111)
    ax.axis('off')

    #if any of the diagonal elements are non-zero, then the adjacency matrix has been squared
    diag_max = np.max(np.diagonal(adjacency_matrix))
    if diag_max > 0:
        squared = True
    else:
        squared = False

    if squared:
        save_images('small-world-matrix-squared.png')
    else:
        save_images('small-world-matrix.png')

    plt.show()

def names_to_matrix_image(card_names: list[str], squared: bool = False) -> None:
    """
    Converts a list of card names into a matrix image.

    Parameters:
        card_names (list): A list of card names.
        squared (bool, optional): If True, the image is saved with name referring to the squared adjacency matrix. Default is False.
    """
    card_images = names_to_images(card_names)
    df_deck = sw.monster_names_to_df(card_names).reset_index(drop=True)
    adjacency_matrix = sw.df_to_adjacency_matrix(df_deck, squared=squared)
    cards_and_matrix_to_image(adjacency_matrix, card_images)

def ydk_to_matrix_image(ydk_file: str, squared: bool = False) -> None:
    """
    Converts a ydk file into a matrix image.

    Parameters:
        ydk_file (str): Path to the ydk file of the deck.
        squared (bool, optional): If True, the image is saved with name referring to the squared adjacency matrix. Default is False.
    """
    card_names = sw.ydk_to_monster_names(ydk_file)
    names_to_matrix_image(card_names, squared=squared)