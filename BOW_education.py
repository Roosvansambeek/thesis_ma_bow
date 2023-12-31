from sklearn.feature_extraction.text import CountVectorizer
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import os
from sqlalchemy import create_engine, Column, String, text, column, String
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel, cosine_similarity
import numpy as np
import pandas as pd

db_connection_string = os.environ['DB_CONNECTION_STRING']

engine = create_engine(
  db_connection_string,
  connect_args={
    "ssl": {
      "ssl_ca": "/etc/ssl/cert.pem"
    }
  }
)



Base = declarative_base()

class Cinfo(Base):
  __tablename__ = 'r_courses' 

  content = Column(String, primary_key=True)
  course_code = Column(String, primary_key=True)
  course_name = Column(String, primary_key=True)

Session = sessionmaker(bind=engine)
session = Session() 

# Fetch data from the r_views table
course_contents = session.query(Cinfo.content, Cinfo.course_code, Cinfo.course_name).all()

course_contents_df = pd.DataFrame(course_contents, columns=['course_content', 'course_code', 'course_title'])

# Create indices
indices = pd.Series(course_contents_df.index, index=course_contents_df['course_code']).drop_duplicates()


course_contents = [row[0] for row in course_contents]
count_vectorizer = CountVectorizer(stop_words='english')
course_content_matrix = count_vectorizer.fit_transform(course_contents)

# Close the session
session.close()

def recs_on_education_BOW(student_number):
  
    Base = declarative_base()
    
    class Cedu(Base):
        __tablename__ = 'r_users'  
    
        student_number = Column(String, primary_key=True)
        education = Column(String, primary_key=True)
    
    Session = sessionmaker(bind=engine)
    session = Session()
    
    
    education_list = session.query(Cedu.student_number, Cedu.education).all()
    
    
    session.close()
    
    user_education_list = [
      {'student_number': student_number, 'user_education': education}
        for student_number, education in education_list
      ]
    
    
  
    education_dict = {}

    # Find the user_interest_vector for the specified student_number
    for user in user_education_list:
        education_terms = user['user_education'].split()  # Split the string into terms

        # Update the dictionary with terms from each user's education
        for term in education_terms:
            
            if term not in education_dict:
                education_dict[term] = 1

    user_education_vector = [education_dict.get(edu, 0) for edu in count_vectorizer.get_feature_names_out()]
    #print('edu_intsss', education_dict)

    similarities = cosine_similarity([user_education_vector], course_content_matrix)

    course_indices = similarities.argsort()[0][::-1]


      
    top_n = 6
    recommended_courses = course_contents_df.iloc[course_indices[:top_n]]


    student_recommendations = {
        "student_number": student_number,
        "recommended_courses": [
            {
                "course_code": course["course_code"],
                "course_content": course["course_content"],
                "course_title": course["course_title"],
                "similarity_score": similarities[0, index]
            }
            for index, course in recommended_courses.iterrows()
        ]
    }


      
    return student_recommendations




def get_ratings_from_database(student_number):
  with engine.connect() as conn:
      query = text("SELECT course_code, rating FROM r_favorites4 WHERE student_number = :student_number")
      result = conn.execute(query, {"student_number": student_number})

     
      ratings = {row.course_code: row.rating for row in result}
  return ratings




def get_recommendations_edu_with_ratings_BOW(student_number):
  recommendations = recs_on_education_BOW(student_number)  
  rated_courses = get_ratings_from_database(student_number)  
  

  for recommendation_set in recommendations['recommended_courses']:
    course_code = recommendation_set['course_code']  
    
    if course_code in rated_courses:
        recommendation_set['rating'] = rated_courses[course_code]
        
    else:
             
      recommendation_set['rating'] = 'off'


  return recommendations




