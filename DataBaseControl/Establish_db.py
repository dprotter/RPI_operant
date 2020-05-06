
from numpy import genfromtxt

from datetime import datetime
from sqlalchemy import Column, Integer, Float, Date, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
import pandas as pd

if __name__ == "__main__":

    path = os.getcwd()

    Base = declarative_base()

    df = pd.read_csv('Test_CSV.csv')
    cd
    #Create the database
    engine = create_engine(f'sqlite:///home/pi/DatabaseTest/Experiment_timeline.db')
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
