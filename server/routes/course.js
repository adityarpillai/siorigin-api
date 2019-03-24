const express = require('express');
const router = express.Router();

const data = require('./../database/s19.min.json');
const dataLength = data.length;

/* GET all courses listing. */
router.get('/', (req, res) => {
  return res.json(data);
});

/* GET data about a specific course */
router.get('/number/', (req, res) => {
  let { courseNumber } = req.query;
  courseNumber = courseNumber.replace(/[.,\/#!$%\^&\*;:{}=\-_`~() ]/g,"");
  courseNumber = courseNumber.toLowerCase();

  let result = [];
  for (let i = 0; i < dataLength; i++) {
    let curr = data[i];
    let c_num = curr['course_number'];
    c_num = c_num.replace(/[.,\/#!$%\^&\*;:{}=\-_`~() ]/g,"");
    c_num = c_num.toLowerCase();

    if (c_num.includes(courseNumber))
      result.push(curr)
  }
  return res.json(result);
});

/* GET data about a specific department */
router.get('/department/', (req, res) => {
  let { courseDepartment } = req.query;
  courseDepartment = courseDepartment.replace(/[.,\/#!$%\^&\*;:{}=\-_`~() ]/g,"")
  courseDepartment = courseDepartment.toLowerCase();

  let result = [];
  for (let i = 0; i < dataLength; i++) {
    let curr = data[i]
    let c_dep = curr['course_department']
    c_dep = c_dep.replace(/[.,\/#!$%\^&\*;:{}=\-_`~() ]/g,"");
    c_dep = c_dep.toLowerCase();

    if (c_dep.includes(courseDepartment))
      result.push(curr)
  }
  return res.json(result);
});


module.exports = router;
