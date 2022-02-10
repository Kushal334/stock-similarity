import logging
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine
import pandas as pd
from config import SQLALCHEMY_DATABASE_URI

app = Flask("recommender_api")
app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
from model_db import UserInstruments

engine = create_engine(SQLALCHEMY_DATABASE_URI)


@app.route('/')
def health():
    return 'OK'


@app.route('/add/request', methods=['POST'])
def post_new_req():
    if request.method == 'POST':
        data = request.get_json()
        new_req = UserInstruments(
            userid=data['userid'], instrid=data['instrid'], price=data['price'], timestamp=data['timestamp']
        )
        df = pd.DataFrame([new_req.to_dict()])
        # df = df.set_index('userid')
        df.to_sql('UserInstruments', con=engine, if_exists='append', index=False)
        return jsonify(resp=data)

    return jsonify(resp={"error": "bad request"})


@app.route('/instruments/<int:instrid>')
def get_top_items_by_min(instrid):

    # FUTURE: Loaded the entire table, which can be cached once for faster queries. Alternative: WHERE clause on instrid
    item_data = pd.read_sql(sql="SELECT * FROM UserInstruments", con=engine, index_col='instrid')

    # Check that instrument exists:
    try:
        item_data.loc[instrid]
    except:
        return jsonify({"error": "The item does not exist"})

    item_data['datetime'] = pd.to_datetime(item_data['timestamp'], unit='s')
    item_data_agg = item_data.loc[instrid].groupby(['instrid', pd.Grouper(key='datetime', freq='T')]) \
        .agg(price_open=pd.NamedAgg(column='price', aggfunc='first'),
             price_close=pd.NamedAgg(column='price', aggfunc='last'),
             price_high=pd.NamedAgg(column='price', aggfunc='max'),
             price_low=pd.NamedAgg(column='price', aggfunc='min')) \
        .reset_index()
    top_5_prices = item_data_agg.sort_values('datetime', ascending=False).head(5)
    top_5_prices['datetime'] = top_5_prices['datetime'].dt.strftime('%Y-%m-%d %H:%M:%S')
    top_5_prices = top_5_prices.set_index('datetime').to_dict('index')
    return jsonify(top_5_prices)


# PREDICTIONS

@app.route('/instruments/similar/<string:userid>')
def get_item_predictions_by_user(userid):
    """
    user: str user id
    predictions: pd.DataFrame of userid/instrid with predictions 'score'
    n_preds: int number of predictions to return
    not_seen: bool flag to return user seen predictions or not
    """
    # FUTURE: Loaded entire tables, which can be cached once for faster queries. Alternative: WHERE clause on userid
    user_data = pd.read_sql(sql="SELECT * FROM UserInstruments", con=engine)
    user_data = user_data.set_index('userid')
    # Check if that user exists:
    try:
        user_data.loc[userid]
    except:
        return jsonify({"error": "The user does not exist"})

    n_preds = 10
    not_seen = True
    predictions = pd.read_sql(sql="SELECT * FROM UserItemSimilarity", con=engine)
    predictions = predictions.set_index('userid')
    try:
        print(predictions.loc[userid])
        user_predictions = predictions.loc[userid].sort_values(ascending=False).rename_axis('instrid').reset_index()
    except KeyError:
        return jsonify({"error": "Prediction scores not generated for new user. Please retrain model!"})
    user_products = user_data.loc[userid]['instrid']
    if not type(user_products) == list:
        user_products = [user_products]
    if not_seen:
        user_predictions = user_predictions[~user_predictions['instrid'].isin(user_products)]
    user_predicted_items = user_predictions[:n_preds]['instrid'].values.tolist()
    return jsonify({"predicted_items_by_user": user_predicted_items})


@app.route('/instruments/similar/<int:instrid>')
def get_item_predictions(instrid):
    # FUTURE: Loaded entire tables, which can be cached once for faster queries. Alternative: WHERE clause on instrid

    item_data = pd.read_sql(sql="SELECT * FROM UserInstruments", con=engine, index_col='instrid')

    # Check that instrument exists:
    try:
        item_data.loc[instrid]
    except:
        return jsonify({"error": "The item does not exist"})

    top_n = 10
    item_similarities = pd.read_sql(sql="SELECT * FROM ItemSimilarity", con=engine)
    item_similarities = item_similarities.set_index('instrid')
    try:
        items_keep = item_similarities.loc[instrid][item_similarities.loc[instrid] > 0]
    except KeyError:
        return jsonify({"error": "Prediction scores not generated for new item. Please retrain model!"})
    print(items_keep)
    predicted_items = items_keep.sort_values(ascending=False)[:top_n].index.tolist()
    return jsonify({"predicted_items": predicted_items})


if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
