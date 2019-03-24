const express = require('express');
const router = express.Router();

const data = require('./../database/s19.min.json');
const dataLength = data.length;


/* GET courses with a specific instructor */
router.get('/name/', (req, res) => {
  let { instructorName } = req.query;
  instructorName = instructorName.replace(/[.,\/#!$%\^&\*;:{}=\-_`~() ]/g,"");
  instructorName = instructorName.toLowerCase();

  let result = [];
  for (let i = 0; i < dataLength; i++) {
    let curr_course = data[i];
    course_section_loop:
    for (let j = 0; j < curr_course['course_sections'].length; j++) {
      let curr_section = curr_course['course_sections'][j]
      let l = curr_section['course_instructors'].length
      for (let k = 0; k < l; k++) {
        let i_name = curr_section['course_instructors'][k]['instructor_name'];
        i_name = i_name.replace(/[.,\/#!$%\^&\*;:{}=\-_`~() ]/g,"");
        i_name = i_name.toLowerCase();
        if (i_name.includes(instructorName)) {
          result.push(curr_course);
          break course_section_loop;
        }
      }
    }
  }
  return res.json(result);
});

module.exports = router;
