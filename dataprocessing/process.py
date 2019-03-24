import argparse
import coursescraper
import json 
import os

# imports used for multithreading
import threading
from queue import Queue
from os import cpu_count
from queue import Empty


def main():
  parser = argparse.ArgumentParser(
    description="Create a JSON file for SIOrigin's frontend.")
  parser.add_argument("semester", metavar="SEMESTER", type=str, 
    help="The school semester for which you wish to retrieve scheduling data. "
      + "It must be one of S, M1, M2, or F.")
  parser.add_argument("csvpath", metavar="FCE_FOLDER", 
    help="Folder containing CSV files to parse for FCE data.")
  parser.add_argument("destination_file", metavar="DESTINATION_FILE",
    help="Name of the destination for the JSON file (without .JSON)")

  args = vars(parser.parse_args())

  scrubbed_data = []



  fce_data = process_fces(args['csvpath'])
  soc_data = collect_schedule(args['semester'])

  data = []

  count = cpu_count()
  lock = threading.Lock()
  queue = Queue()

  if count is None:
      count = 4

  instructor_ratings = {}


  for course in soc_data['courses']:
      queue.put(course)

  num_processed = 0
  queue_size = queue.qsize()

  def run_fce_processing():
    while True:
      try:
        course_num = queue.get(timeout=4)
      except Empty:
        return

      nonlocal num_processed 

      with lock:
        num_processed += 1

      if True:
        print("\r[{}/{}]: Processing FCEs for {}".format(
          num_processed, queue_size, course_num), end="")

      nonlocal instructor_ratings

      c_data = course_processor(course_num, soc_data['courses'][course_num],
       fce_data, instructor_ratings, lock)

      with lock:
        data.append(c_data)
      
      queue.task_done()

  print("Running FCE processing on " + str(count) + " threads")
  for _ in range(count):
      thread = threading.Thread(target=run_fce_processing)
      thread.setDaemon(True)
      thread.start()

  queue.join()

  print("")

  # Dump minified
  with (open(os.path.abspath("{}.min.json".format(args['destination_file'])), 
    'w')) as outfile:
    print("Writing minified JSON")
    json.dump(data, outfile)

  # Dump pretty
  with open(os.path.abspath("{}.json".format(args['destination_file'])), 'w') as outfile:
    print("Writing JSON")
    json.dump(data, outfile, indent=2)


  fce_data = process_fces(args['csvpath'])

def collect_schedule(semester):
  return coursescraper.get_course_data(semester)

def process_fces(csvpath):
  return coursescraper.parse_fces(csvpath)

def course_processor(course_num, soc_data, fce_data, instructor_ratings,
  lock):
  
  # print("Processing course {}...".format(course_num))

  def get_instructor_data(instructors):
    instructor_data = []
    for instructor_name in instructors:
      instructor_obj = {}
      instructor_obj['instructor_name'] = instructor_name
      
      if instructor_name in instructor_ratings:
        overall_rating = instructor_ratings[instructor_name]['rating']
        overall_hours = instructor_ratings[instructor_name]['hours']
      else:
        # FCE Ratings
        respondent_count = 0
        overall_rating = 0
        overall_hours = 0

        for poll in fce_data:
          if ('Name' in poll and 'Num Respondents' in poll and
            'Overall course rate' in poll and 'Hrs Per Week' in poll and
            poll['Name'].lower() == instructor_name.lower() and
            poll['Num Respondents'] is not None and 
            poll['Overall course rate'] is not None and
            poll['Hrs Per Week'] is not None):

            overall_rating += (poll['Num Respondents'] *
              poll['Overall course rate'])
            
            overall_hours += (poll['Num Respondents'] * poll['Hrs Per Week'])

            respondent_count += poll['Num Respondents']

        if respondent_count != 0:
          overall_rating /= float(respondent_count)
          overall_hours /= float(respondent_count)
        else:
          overall_rating = None
          overall_hours = None

        with lock: 
          instructor_ratings[instructor_name] = {
            'rating': overall_rating,
            'hours': overall_hours
          }

      instructor_obj['instructor_rating'] = overall_rating
      instructor_obj['instructor_hours'] = overall_hours

      instructor_data.append(instructor_obj)

    return instructor_data

  def seconds_since_sunday_midnight(day, time):
    from datetime import datetime

    t = datetime.strptime(time, '%I:%M%p')

    delta = (t - t.replace(hour=0, minute=0, second=0)).total_seconds()
    delta += (day * 86400)
    return int(delta)

  def get_lecture_times(lectures):
    lecture_times = []

    for time in lectures:
      if time['days'] == None:
        lecture_time_obj = {}
        lecture_time_obj['start_time'] = None
        lecture_time_obj['end_time'] = None
        lecture_time_obj['lecture_building'] = time['building']
        lecture_time_obj['lecture_room'] = time['room']
        lecture_times.append(lecture_time_obj)
      else: 
        for day in time['days']:
          # Set lecture time details
          lecture_time_obj = {}
          st = seconds_since_sunday_midnight(day, time['begin'])
          lecture_time_obj['start_time'] = st
          et = seconds_since_sunday_midnight(day, time['end'])
          lecture_time_obj['end_time'] = et
          lecture_time_obj['lecture_building'] = time['building']
          lecture_time_obj['lecture_room'] = time['room']

          # Set campus both here and in the outside file
          lecture_time_obj['campus'] = time['location']
          section_data['campus'] = time['location']

          # Add the data!
          lecture_times.append(lecture_time_obj)

    return lecture_times

  def get_section_times(sections):
    section_times = []

    for time in sections:
      if time['days'] == None:
        section_time_obj = {}
        section_time_obj['start_time'] = None
        section_time_obj['end_time'] = None
        section_time_obj['section_building'] = time['building']
        section_time_obj['section_room'] = time['room']
        section_times.append(section_time_obj)
      else:  
        for day in time['days']:
          # Set section time details
          section_time_obj = {}
          st = seconds_since_sunday_midnight(day, time['begin'])
          section_time_obj['start_time'] = st
          et = seconds_since_sunday_midnight(day, time['end'])
          section_time_obj['end_time'] = et
          section_time_obj['section_building'] = time['building']
          section_time_obj['section_room'] = time['room']

          section_times.append(section_time_obj)

    return section_times

  sections_list = []
  # print(soc_data)
  for lecture in soc_data['lectures']:
    if len(soc_data['sections']) == 0:
      
      # LECTURE ONLY CLASS
      # Set up information
      section_data = {}
      section_data['course_lecture'] = lecture['name']
      section_data['course_section'] = ""

      # Calculate instructor information
      instructor_data = get_instructor_data(lecture['instructors'])
      section_data['course_instructors'] = instructor_data 

      # Calculate lecture tiems
      lecture_times = get_lecture_times(lecture['times'])
      section_data['lecture_times'] = lecture_times

      # Section times are just empty :)
      section_data['section_times'] = []

      sections_list.append(section_data)

    else:
      for section in soc_data['sections']:      
       
        # LECTURE AND SECTION CLASS
        # Set up information
        section_data = {}
        section_data['course_lecture'] = lecture['name']
        section_data['course_section'] = section['name']

        # Calculate instructor information
        instructor_data = get_instructor_data(lecture['instructors'])
        section_data['course_instructors'] = instructor_data

        # Calculate lecture times
        lecture_times = get_lecture_times(lecture['times'])
        section_data['lecture_times'] = lecture_times

        # Calculate section times
        section_times = get_section_times(section['times'])
        section_data['section_times'] = section_times

        sections_list.append(section_data)

  
  # FCE ratings for course
  overall_rating = 0
  overall_hours = 0
  respondent_count = 0

  for poll in fce_data:
    if ('Course ID' in poll and poll['Course ID'] == course_num and
      'Hrs Per Week' in poll and 'Num Respondents' in poll and
      'Overall course rate' in poll):
      hrs_per_week = poll['Hrs Per Week']
      num_respondents = poll['Num Respondents']
      overall_course_rate = poll['Overall course rate']
      if (hrs_per_week is not None and 
        num_respondents is not None and
        overall_course_rate is not None):
        
        overall_rating += num_respondents * overall_course_rate
        overall_hours += num_respondents * hrs_per_week
        respondent_count += num_respondents

  if respondent_count != 0:
    overall_rating /= float(respondent_count)
    overall_hours /= float(respondent_count)
  else:
    overall_rating = None
    overall_hours = None

  res = {
    "course_number": course_num,
    "course_name": soc_data['name'],
    "course_units": soc_data['units'],
    "course_description": soc_data['desc'],
    "course_department": soc_data['department'],
    "course_rating": overall_rating,
    "course_hours": overall_hours,
    "course_sections": sections_list,
  }

  return res


if __name__ == "__main__":
  main()