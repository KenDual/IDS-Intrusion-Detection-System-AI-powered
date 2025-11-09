import pickle
with open('ml/models/xgboost_model.pkl', 'rb') as f:
    model = pickle.load(f)
    print("Type:", type(model))
    print("Has predict_proba?", hasattr(model, 'predict_proba'))
    print("Has predict?", hasattr(model, 'predict'))