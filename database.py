from sqlalchemy import create_engine
from sqlalchemy import text
from sqlalchemy.orm import sessionmaker
import os


# Rest of your code remains the same

db_connection_string = os.environ['DB_CONNECTION_STRING']

engine = create_engine(
  db_connection_string,
  connect_args={
    "ssl": {
      "ssl_ca": "/etc/ssl/cert.pem"
    }
  }
)

def load_courses_from_db():
  with engine.connect() as conn:
    result = conn.execute(text("SELECT * FROM courses"))
    courses = []
    columns = result.keys()
    for row in result:
      result_dict = {column: value for column, value in zip(columns, row)}
      courses.append(result_dict)
    return courses


def load_carousel_courses_from_db(student_number):
  with engine.connect() as conn:
      query = text("""
          SELECT c.*, rf.rating 
          FROM courses c
          LEFT JOIN r_favorites4 rf
          ON c.course_code = rf.course_code AND rf.student_number = :student_number
          WHERE c.site_placement = 'Carousel'
      """)

      result = conn.execute(query, {"student_number": student_number})

      carousel_courses = []
      columns = result.keys()
      for row in result:
          result_dict = {column: value for column, value in zip(columns, row)}
          carousel_courses.append(result_dict)

      return carousel_courses

def load_best_courses_from_db():
  with engine.connect() as conn:
      result = conn.execute(text("SELECT * FROM courses WHERE site_placement = 'Best'"))
      best_courses = []
      columns = result.keys()
      for row in result:
          result_dict = {column: value for column, value in zip(columns, row)}
          best_courses.append(result_dict)
      return best_courses



def load_best_courses_with_favorite_from_db(student_number):
  with engine.connect() as conn:
      query = text("""
          SELECT c.*, rf.rating 
          FROM courses c
          LEFT JOIN r_favorites4 rf
          ON c.course_code = rf.course_code AND rf.student_number = :student_number
          WHERE c.site_placement = 'Best'
      """)
    
      result = conn.execute(query, {"student_number": student_number})

      best_courses = []
      columns = result.keys()
      for row in result:
          result_dict = {column: value for column, value in zip(columns, row)}
          best_courses.append(result_dict)

      return best_courses

def add_test_to_db(request, student_number, course_code, favorite_value):
  with engine.connect() as conn:
      # Check if the record already exists
      existing_record = conn.execute(
          text("SELECT * FROM r_favorites4 WHERE course_code = :course_code AND student_number = :student_number"),
          {"course_code": course_code, "student_number": student_number}
      ).fetchone()

      if existing_record:
          # Update the existing record
          query = text("UPDATE r_favorites4 SET rating = :rating WHERE course_code = :course_code AND student_number = :student_number")
      else:
          # Insert a new record
          query = text("INSERT INTO r_favorites4 (course_code, student_number, rating) VALUES (:course_code, :student_number, :rating)")

      conn.execute(query, {"course_code": course_code, "student_number": student_number, "rating": favorite_value})


def get_test_from_db(student_number, course_code):
  with engine.connect() as conn:
      query = text("SELECT favorite FROM new_test WHERE student_number = :student_number AND course_code = :course_code")
      result = conn.execute(query, student_number=student_number, course_code=course_code)
      row = result.fetchone()
      if row is not None and len(row) > 0:
          favorite_value = row[0]
          return favorite_value
      return None  # Handle the case where no data is found


def load_favorite_courses_from_db(student_number):
    with engine.connect() as conn:
      query = text(""" 
          SELECT rf.*, c.course_code, c.course_name, c.content
          FROM courses c
          LEFT JOIN r_favorites4 rf
          ON c.course_code = rf.course_code AND rf.student_number =:student_number
          WHERE rf.rating = 'on' 
      """)
      
      result = conn.execute(query, {"student_number": student_number})
      
      favorite_courses = []
      columns = result.keys()
      for row in result:
          result_dict = {column: value for column, value in zip(columns, row)}
          favorite_courses.append(result_dict)
      return favorite_courses



def put_rating_to_db(course_code, student_number, data):
  with engine.connect() as conn:
    conn.execute(
        text("""
        INSERT INTO r_favorites (student_number, course_code, rating)
        VALUES (:student_number, :course_code, :rating)"""),
        {"student_number": student_number, "course_code": course_code, "rating": data['favorite']}
    )

    
  
# Check if each course is a favorite for the current user
# and render the star form accordingly

def add_rating_to_db(course_code, student_number, data):
  with engine.connect() as conn:
      conn.execute(
          text("""
          INSERT INTO r_favorites (course_code, student_number, rating)
          VALUES (:course_code, :student_number, :rating)
          ON DUPLICATE KEY UPDATE rating = :rating
          """),
          {"student_number": student_number, "course_code": course_code, "rating": data['favorite']}
      )

def remove_rating_from_db(course_code, student_number):
  with engine.connect() as conn:
      conn.execute(
          text("UPDATE r_favorites SET rating = 0 WHERE course_code = :course_code AND student_number = :student_number"),
          {"course_code": course_code, "student_number": student_number}
      )



def add_login_to_db(student_number, password, level, education):
  with engine.connect() as conn:
      conn.execute(
          text("INSERT INTO r_users (student_number, password, level, education) VALUES (:student_number, :password, :level, :education)"),
          {"student_number": student_number, "password": password, "level": level, "education": education}
      )

def check_credentials(student_number, password):
  with engine.connect() as conn:
      result = conn.execute(
          text("SELECT * FROM r_users WHERE student_number = :student_number AND password = :password"),
          {"student_number": student_number, "password": password}
      )
      return result.fetchone() is not None

def add_interests_to_db(data):
  with engine.connect() as conn:
      query = text("INSERT INTO r_users (marketing, economics, management, sustainability, biology, politics, law, communication, Bachelor, Master) "
                   "VALUES (:marketing, :economics, :management, :sustainability, :biology, :politics, :law, :communication, :Bachelor, :Master)")

      # Construct the parameter dictionary
      params = {
          'marketing': data.get('marketing'),
          'economics': data.get('economics'),
          'management': data.get('management'),
          'sustainability': data.get('sustainability'),
          'biology': data.get('biology'),
          'politics': data.get('politics'),
          'law': data.get('law'),
          'communication': data.get('communication'),
          'Bachelor': data.get('Bachelor'),
          'Master': data.get('Master')
      }

      conn.execute(query, params)


def update_interests(student_number, password, data):
  with engine.connect() as conn:
      query = text(
          "UPDATE r_users SET "
          "marketing = :marketing, "
          "economics = :economics, "
          "management = :management, "
          "sustainability = :sustainability, "
          "biology = :biology, "
          "politics = :politics, "
          "law = :law, "
          "communication = :communication, "
          "Bachelor = :Bachelor, "
          "Master = :Master "
              "WHERE student_number = :student_number AND password = :password"
          )
# Add student_number and password to the parameter dictionary
      params = {
          'marketing': data.get('marketing'),
          'economics': data.get('economics'),
          'management': data.get('management'),
          'sustainability': data.get('sustainability'),
          'biology': data.get('biology'),
          'politics': data.get('politics'),
          'law': data.get('law'),
          'communication': data.get('communication'),
          'Bachelor': data.get('Bachelor'),
          'Master': data.get('Master'),
          'student_number': student_number,
          'password': password
      }

      conn.execute(query, params)



def add_views_to_db(student_number, course_code, timestamp):
  with engine.connect() as conn:
      query = text("INSERT INTO r_views (student_number, course_code, timestamp) VALUES (:student_number, :course_code, :timestamp)")
      conn.execute(query, {"student_number": student_number, "course_code": course_code, "timestamp": timestamp})




