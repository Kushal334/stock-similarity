import logging, os, sys
import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import pairwise_distances
from sqlalchemy import create_engine

sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
from config import PROJECT_ROOT, SQLALCHEMY_DATABASE_URI
sys.path.append(PROJECT_ROOT)

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
logger.setLevel('INFO')
engine = create_engine(SQLALCHEMY_DATABASE_URI)


def get_data(table: str):
    df = pd.read_sql(sql="SELECT * FROM UserInstruments", con=engine)
    return df


#################################
# User Based Collaborative Model
#################################

def _user_data_preparation(data: pd.DataFrame):
    item_count_df = data.groupby(['userid', 'instrid']).agg({'instrid': 'count'}).rename(columns={'instrid': 'instr_count'})
    item_count_df = item_count_df.reset_index()
    user_products_df = item_count_df.pivot(index='userid', columns='instrid', values='instr_count').fillna(0)
    return user_products_df


def _euclidean_distance_user_model(user_item_df: pd.DataFrame):
    item_similarity = pairwise_distances(user_item_df.values.T, metric='euclidean')
    user_predictions = user_item_df.values.dot(item_similarity) / np.abs(item_similarity.sum(axis=1))
    user_predictions = 1 / (1 + user_predictions)
    return pd.DataFrame(user_predictions, columns=user_item_df.columns, index=user_item_df.index)


def generate_user_model(data: pd.DataFrame):
    user_products_df = _user_data_preparation(data)
    predictions_df = _euclidean_distance_user_model(user_products_df)
    return predictions_df


def save_db_user_recs(predictions_df, table):
    predictions_df.to_sql(name=table, con=engine, if_exists='append')


#################################
# Item Based Collaborative Model
#################################

def _item_data_preparation(data: pd.DataFrame):
    item_count_df = data.groupby(['userid', 'instrid']).agg({'instrid': 'count'}).rename(columns={'instrid': 'item_count'})
    item_count_df = item_count_df.reset_index()
    item_user_df = item_count_df.pivot(index='instrid', columns='userid', values='item_count').fillna(0)
    return item_user_df


def _cosine_distance_model(item_user_df: pd.DataFrame):
    item_distances = pairwise_distances(item_user_df.values, metric='cosine')
    item_similarity = 1 - item_distances
    np.fill_diagonal(item_similarity, 0)
    return pd.DataFrame(item_similarity, columns=item_user_df.index, index=item_user_df.index)


def generate_item_model(data: pd.DataFrame):
    item_user_data = _item_data_preparation(data)
    item_similarity = _cosine_distance_model(item_user_data)
    return item_similarity


def save_db_item_recs(item_similarity, table):
    item_similarity.to_sql(name=table, con=engine, if_exists='append')


# Load the data and prepare the user model
logger.info("Generating user predictions...")
user_data = get_data('UserInstruments')
user_data = user_data.set_index('userid')
user_predictions = generate_user_model(user_data)
save_db_user_recs(user_predictions, 'UserItemSimilarity')


logger.info("Generating item predictions...")
item_data = get_data('UserInstruments')
item_similarities = generate_item_model(item_data)
save_db_item_recs(item_similarities, 'ItemSimilarity')
item_data = item_data.set_index('instrid')

logger.info("Data and model generated successfully!")
