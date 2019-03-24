"""aggregate.py

One script to rule them all

Downloads schedule data for a specific semester, including course meeting times,
course descriptions, pre/corequisites, FCEs, and so on.

Attributes:
    SEMESTER_ABBREV (object): Contains abbreviations for each semester
    SOURCES (TYPE): Description

Aditya Pillai (apillai@andrew.cmu.edu)
2019-03-10
"""

import json
import os.path
from datetime import date
from coursescraper.parse_descs import get_course_desc
from coursescraper.parse_schedules import parse_schedules

# imports used for multithreading
import threading
from queue import Queue
from os import cpu_count
from queue import Empty


# Constants
SOURCES = os.path.join(os.path.dirname(__file__), 'data/schedule_pages.txt')
SEMESTER_ABBREV = {
    'Spring': 'S',
    'Fall': 'F',
    'Summer': 'M'
}


def aggregate(schedules, threads=None):
    """aggregate

    Combines the course descriptions and schedules into one object.
    
    Args:
        schedules (object): Course schedules object as returned by parse_descs
    
    Returns:
        Object: an object containing the aggregate of the three datasets
    """
    courses = {}

    semester = schedules['semester'].split(' ')[0]
    semester = SEMESTER_ABBREV[semester]
    year = schedules['semester'].split(' ')[-1][2:]

    count = cpu_count()
    lock = threading.Lock()
    queue = Queue()

    if count is None:
        count = 4

    if threads is not None:
        print("Manually set to {} thread(s)...".format(threads))
        count = threads


    for course in schedules['schedules']:
        queue.put(course)

    fces_processed = 0
    queue_size = queue.qsize()

    def run():
        while True:
            try:
                course = queue.get(timeout=4)
            except Empty:
                return

            nonlocal fces_processed
            nonlocal queue_size

            with lock:
                fces_processed += 1

            if True:
                print('\r[{}/{}]: Getting description for {}...'.format(
                    fces_processed, queue_size, course['num']), end="")

            desc = get_course_desc(course['num'], semester, year)
            desc['name'] = course['title']

            try:
                desc['units'] = float(course['units'])
            except ValueError:
                desc['units'] = None

            desc['department'] = course['department']
            desc['lectures'] = course['lectures']
            desc['sections'] = course['sections']
            names_dict = desc.pop('names_dict', {})

            for key in ('lectures', 'sections'):
                for meeting in desc[key]:
                    if meeting['name'] in names_dict:
                        meeting['instructors'] = names_dict[meeting['name']]

            number = course['num'][:2] + '-' + course['num'][2:]
            with lock:
                courses[number] = desc
            queue.task_done()

    print("Running course description processing on " + str(count) + " threads")
    for _ in range(count):
        thread = threading.Thread(target=run)
        thread.setDaemon(True)
        thread.start()

    queue.join()

    print("")

    return {'courses': courses, 'rundate': str(date.today()),
            'semester': schedules['semester']}



def get_course_data(semester, threads=None):
    """get_course_data
    
    Used for retrieving all information from the course-api for a given
    semester.

    Args:
        semester (str): The semester to get data for. Must be one of [S, M1,
        M2, F].
    
    Returns:
        Object: An object containing all course-api data -- see README.md for
        more information.
    """
    schedules = parse_schedules(semester)
    return aggregate(schedules, threads)
