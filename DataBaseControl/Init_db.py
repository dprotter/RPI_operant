
from numpy import genfromtxt

from datetime import datetime
from sqlalchemy import Column, Integer, Float, Date, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
import pandas as pd


def init_db(file_location, database_target_loc):
    Base = declarative_base()

    df = pd.read_csv(file_location)
    cd
    #Create the database
    engine = create_engine(f'sqlite://{database_target_loc}')
    Base.metadata.create_all(engine)

    #Create the session
    session = sessionmaker()
    session.configure(bind=engine)
    s = session()

    try:
        df.to_sql("experimental_timetable",
                    engine,
                    if_exists='replace',
                    index=True,
                    schema='public',
                    chunksize = 500,
                    dtype={'date': DateTime,
                            'run_time': DateTime,
                            'vole': Integer,
                            'script': String(50),
                            'user': String(50),
                            'rounds': Integer,
                            'rounds_completed': Integer,
                            'done': Boolean,})

    except:

        print('woah woah woah, we had a problem making your DB!')

    

    
