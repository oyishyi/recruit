from flask_sqlalchemy import SQLAlchemy
#need to be installed
import spacy

db =  SQLAlchemy()
nlp = spacy.load('en_core_web_md')
