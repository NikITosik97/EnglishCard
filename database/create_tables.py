import sqlalchemy

from sqlalchemy.orm import sessionmaker
from database.config import DSN
from database.models import create_tables


engine = sqlalchemy.create_engine(DSN)
create_tables(engine)

Session = sessionmaker(bind=engine)
session = Session()





