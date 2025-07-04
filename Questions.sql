## -- SQL Query Questions for School Records Database

-- This file lists a series of questions (basic to advanced) to answer against the
-- School Records schema (tables: students, academic, graduates, terminated, grades).
--------------------------------------------------------------------------------------

-- 1. Basic SELECT & FILTER
-- 1. List every student’s student_id, first_name, last_name, enrollment_year, and enrollment_status.

-- 2. Find students who enrolled in a specific year, e.g. 2015.

-- 3. Retrieve all students with enrollment_status = 'transfer-in'.

-- 4. Show all students currently in a given grade, e.g. Grade 5.

-- 5. List students born before a certain date, e.g. January 1, 2005.

----------------------------------------------------------------------

-- 2. Aggregations & GROUP BY
-- 6. Count the total number of students.

-- 7. Calculate the number of students enrolled each year.

-- 8. Determine student counts per grade for the latest academic year.

-- 9. Compute class sizes for a specific year and grade, e.g. Grade 7 in 2024.

-- 10. Count the number of graduates per academic year.
--------------------------------------------------------

-- 3. JOINs & FILTERS
-- 11. Show each student’s name alongside their final percentage for a given year.

-- 12. Identify students whose grade never changed (never promoted).
-- 13. List students who scored above a high threshold, e.g. ≥ 90%, in any year.
-- 14. Find students at risk: those with final percentage below passing in their most recent year.
-- 15. List terminated students along with termination reason and year.
------------------------------------------------------------------------

-- 4. Subqueries & Correlated Filters
-- 16. Identify students whose latest final percentage falls below the average for their grade.
-- 17. Find students whose percentage improved year-over-year (e.g. 2023 vs 2022).
-- 18. List students whose percentage in a given year matches the maximum for their grade and class.
-----------------------------------------------------------------------------------------------------

-- 5. Window Functions
-- 19. Rank students by final percentage within each grade and academic year.
-- 20. Assign percentile or quartile buckets to students within each grade-year.
-- 21. Compute each student’s running average percentage over all years.
-- 22. Calculate the change in percentage from one year to the next for each student.
-- 23. Track cumulative failure counts per student across academic years.
--------------------------------------------------------------------------

-- 6. CTEs & Recursive Queries
-- 24. Use a recursive CTE to trace each student’s grade progression from enrollment onward.
-- 25. Identify students who have failed three consecutive years.
-- 26. Compute annual pass rate (pass count divided by total) per grade-year using a CTE.
------------------------------------------------------------------------------------------

-- 7. PIVOT / UNPIVOT
-- 27. Pivot academic results so each student has columns for each year’s final percentage.
-- 28. Unpivot the grades reference table to list each subject with its mark range.
------------------------------------------------------------------------------------

-- 8. GROUPING SETS & ROLLUP
-- 29. Generate multi-level aggregates of average percentages by grade, class, and overall.
-- 30. Use CUBE to analyze all combinations of grade, class, and academic year.
--------------------------------------------------------------------------------

-- 9. Analytical & Statistical Queries
-- 31. Compute a given percentile (e.g. 90th) of final percentages per grade-year.
-- 32. Calculate standard deviation of scores across students in each grade.
-- 33. Measure correlation between starting grade and final performance.
-------------------------------------------------------------------------

-- 10. Views & Procedures
-- 34. Create a view of active students (excluding graduates and terminated).
-- 35. Develop a parameterized query or stored procedure to fetch the top N students by percentage for any year and grade.
