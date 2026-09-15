SELECT
    role_category,
    COUNT(*) AS postings,
    ROUND(100.0 * AVG(sql), 1) AS pct_sql,
    ROUND(100.0 * AVG(python), 1) AS pct_python,
    ROUND(100.0 * AVG(power_bi), 1) AS pct_power_bi,
    ROUND(100.0 * AVG(tableau), 1) AS pct_tableau,
    ROUND(100.0 * AVG(azure), 1) AS pct_azure,
    ROUND(100.0 * AVG(aws), 1) AS pct_aws,
    ROUND(100.0 * AVG(genai_llm), 1) AS pct_genai_llm
FROM postings
GROUP BY role_category
ORDER BY postings DESC;



SELECT
    role_category,
    COUNT(*) AS salary_observations,
    ROUND(AVG(salary_min), 0) AS avg_salary_min,
    ROUND(AVG(salary_max), 0) AS avg_salary_max
FROM postings
WHERE salary_min IS NOT NULL
   OR salary_max IS NOT NULL
GROUP BY role_category
ORDER BY avg_salary_max DESC;



WITH city_salary AS (
    SELECT
        role_category,
        city,
        COUNT(*) AS postings,
        AVG(salary_max) AS avg_salary_max
    FROM postings
    WHERE salary_max IS NOT NULL
    GROUP BY role_category, city
)
SELECT
    role_category,
    city,
    postings,
    ROUND(avg_salary_max, 0) AS avg_salary_max,
    RANK() OVER (
        PARTITION BY role_category
        ORDER BY avg_salary_max DESC
    ) AS city_rank
FROM city_salary
WHERE postings >= 2
ORDER BY role_category, city_rank;



SELECT
    city,
    role_category,
    COUNT(*) AS posting_count
FROM postings
GROUP BY city, role_category
ORDER BY posting_count DESC;


SELECT
    substr(posted_date, 1, 7) AS month,
    role_category,
    COUNT(*) AS posting_count
FROM postings
WHERE posted_date IS NOT NULL
GROUP BY month, role_category
ORDER BY month, role_category;


SELECT
    company,
    role_category,
    COUNT(*) AS posting_count
FROM postings
WHERE company IS NOT NULL
  AND company <> 'Unknown'
GROUP BY company, role_category
ORDER BY posting_count DESC
LIMIT 25;


SELECT
    role_category,
    COUNT(*) AS postings,
    SUM(CASE WHEN sql = 1 AND python = 1 THEN 1 ELSE 0 END) AS sql_python,
    SUM(CASE WHEN python = 1 AND (aws = 1 OR azure = 1) THEN 1 ELSE 0 END) AS python_cloud,
    SUM(CASE WHEN python = 1 AND genai_llm = 1 THEN 1 ELSE 0 END) AS python_genai
FROM postings
GROUP BY role_category
ORDER BY postings DESC;


WITH monthly_skill AS (
    SELECT
        substr(posted_date, 1, 7) AS month,
        AVG(python) * 100.0 AS pct_mentioning
    FROM postings
    WHERE posted_date IS NOT NULL
    GROUP BY month
)
SELECT
    month,
    ROUND(pct_mentioning, 1) AS pct_mentioning,
    ROUND(
        pct_mentioning - LAG(pct_mentioning) OVER (ORDER BY month),
        1
    ) AS mom_change
FROM monthly_skill
ORDER BY month;





