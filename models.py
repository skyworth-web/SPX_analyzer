from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.postgresql import JSONB

db = SQLAlchemy()

class ComponentRegistry(db.Model):
    __tablename__ = 'component_registry'
    
    id = db.Column(db.Integer, primary_key=True)
    component_type = db.Column(db.String(50))
    instrument = db.Column(db.String(50))
    strategy = db.Column(db.String(50))
    description = db.Column(db.Text)
    status = db.Column(db.String(20))
    config = db.Column(JSONB)
    created_at = db.Column(db.DateTime(timezone=True))
    updated_at = db.Column(db.DateTime(timezone=True))
    component_name = db.Column(db.String(50), unique=True)

class SPXSpot(db.Model):
    __tablename__ = 'spx_0dte_spot'
    
    timestamp = db.Column(db.DateTime(timezone=True), primary_key=True)
    price = db.Column(db.Float)

class SPXOptionStream(db.Model):
    __tablename__ = 'spx_0dte_stream'
    
    timestamp = db.Column(db.DateTime(timezone=True), primary_key=True)
    call_net_chg = db.Column(db.Float)
    call_iv = db.Column(db.Float)
    call_open_int = db.Column(db.Integer)
    call_vega = db.Column(db.Float)
    call_theta = db.Column(db.Float)
    call_gamma = db.Column(db.Float)
    call_delta = db.Column(db.Float)
    call_last = db.Column(db.Float)
    call_ask = db.Column(db.Float)
    call_bid = db.Column(db.Float)
    exp_date = db.Column(db.Date, primary_key=True)
    strike_price = db.Column(db.Float, primary_key=True)
    put_bid = db.Column(db.Float)
    put_ask = db.Column(db.Float)
    put_last = db.Column(db.Float)
    put_delta = db.Column(db.Float)
    put_gamma = db.Column(db.Float)
    put_theta = db.Column(db.Float)
    put_vega = db.Column(db.Float)
    put_open_int = db.Column(db.Integer)
    put_iv = db.Column(db.Float)
    put_net_chg = db.Column(db.Float)

class Position(db.Model):
    __tablename__ = 'positions'
    
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(20))
    short_call_strike = db.Column(db.Float)
    long_call_strike = db.Column(db.Float)
    short_put_strike = db.Column(db.Float)
    long_put_strike = db.Column(db.Float)
    entry_price = db.Column(db.Float)
    entry_time = db.Column(db.DateTime(timezone=True))

class SPXAnalysis(db.Model):
    __tablename__ = 'spx_analysis'
    
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime(timezone=True))
    spx_price = db.Column(db.Float)
    opportunity = db.Column(JSONB)