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
  const { courseNumber } = req.query;
  let result = [];
  for (let i = 0; i < dataLength; i++) {
    let curr = data[i]
    if (curr['course_number'].includes(courseNumber))
      result.push(curr)
  }
  return res.json(result);
});

/* GET data about a specific department */
router.get('/department/', (req, res) => {
  const { courseDepartment } = req.query;
  console.log("Department: " + courseDepartment)
  let result = [];
  for (let i = 0; i < dataLength; i++) {
    let curr = data[i]
    if (curr['course_department'].includes(courseDepartment))
      result.push(curr)
  }
  return res.json(result);
});


module.exports = router;
